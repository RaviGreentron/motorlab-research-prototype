"""Independent behavioral tests of fitting boundaries and reconstruction."""
import pickle
import numpy as np
import pytest
from motorlab.models import Autoencoder, DetectorSuite, FEATURES


def partitions():
    rng = np.random.default_rng(711)
    d = len(FEATURES)
    # Fixed independent healthy partitions, with realistic nonzero feature means.
    center = np.linspace(1, 40, d)
    scale = np.linspace(.1, 2, d)
    return tuple(center + rng.normal(size=(n, d)) * scale for n in (140, 45, 70))


@pytest.fixture(scope='module')
def suite():
    return DetectorSuite(seed=71).fit(*partitions())


def test_scaler_uses_training_only(suite):
    train, early, calibration = partitions()
    np.testing.assert_allclose(suite.scaler.mean_, train.mean(axis=0), atol=1e-12)
    assert suite.scaler.n_samples_seen_ == len(train)
    assert suite.train_count == 140
    assert suite.calibration_count == 70
    before = suite.scaler.mean_.copy()
    suite.score(np.full((7, len(FEATURES)), 10000.))
    np.testing.assert_array_equal(suite.scaler.mean_, before)


def test_calibration_changes_thresholds_not_fitted_models(suite):
    train, early, cal = partitions()
    changed = DetectorSuite(seed=71).fit(train, early, cal + 30.)
    np.testing.assert_array_equal(suite.scaler.mean_, changed.scaler.mean_)
    for a, b in zip(suite.ae.weights, changed.ae.weights):
        np.testing.assert_array_equal(a, b)
    probe = train[:6]
    for key in ('A', 'B', 'C'):
        np.testing.assert_allclose(suite.raw_scores(probe)[key], changed.raw_scores(probe)[key])
    assert changed.thresholds['A'] > suite.thresholds['A'] * 5
    assert changed.thresholds['C'] > suite.thresholds['C'] * 5


def test_independent_calibration_quantile(suite):
    _, _, calibration = partitions()
    values = suite.raw_scores(calibration)
    for name, scores in values.items():
        assert suite.thresholds[name] == pytest.approx(np.quantile(scores, .99))


def test_if_and_statistics_detect_large_out_of_distribution_shift(suite):
    train, _, _ = partitions()
    extreme = train[:20] + 100
    score = suite.score(extreme)
    assert score['A']['alert'].all()
    assert score['B']['alert'].mean() >= .95
    assert score['C']['alert'].all()
    assert np.median(score['B']['raw']) > np.median(suite.score(train[:20])['B']['raw'])
    # Raw scores are unbounded deviations, not failure probabilities.
    assert score['A']['raw'].min() > 1


def test_ae_learns_manifold_deterministically_and_restores_best_checkpoint():
    rng = np.random.default_rng(12)
    z = rng.normal(0, .3, (180, 2))
    projection = rng.normal(size=(2, 6))
    x = z @ projection
    a = Autoencoder(latent=2, epochs=220, seed=11, patience=25).fit(x[:120], x[120:])
    b = Autoencoder(latent=2, epochs=220, seed=11, patience=25).fit(x[:120], x[120:])
    assert a.history[-1]['train_loss'] < a.history[0]['train_loss'] * .25
    assert a.score(x[120:]).mean() == pytest.approx(a.best_validation_loss, abs=1e-12)
    assert a.best_validation_loss <= min(row['validation_loss'] for row in a.history) + 1e-6
    np.testing.assert_array_equal(a.score(x), b.score(x))
    restored = pickle.loads(pickle.dumps(a))
    np.testing.assert_array_equal(a.score(x), restored.score(x))
    assert a.score(np.full((20, 6), 30.)).mean() > a.score(x[120:]).mean() * 10


def test_suite_checkpoint_roundtrip(suite):
    # Serialization is a local trusted artifact; no external pickle is loaded.
    restored = pickle.loads(pickle.dumps(suite))
    probe = partitions()[2][:5]
    assert restored.thresholds == suite.thresholds
    for key in ('A', 'B', 'C'):
        np.testing.assert_array_equal(restored.score(probe)[key]['raw'], suite.score(probe)[key]['raw'])


@pytest.mark.parametrize('partition_index', [0, 1, 2])
def test_invalid_partitions_rejected(partition_index):
    parts = list(partitions())
    parts[partition_index][0, 0] = np.nan
    with pytest.raises(ValueError): DetectorSuite().fit(*parts)
    parts = list(partitions()); parts[partition_index] = parts[partition_index][:9]
    with pytest.raises(ValueError): DetectorSuite().fit(*parts)


def test_statistical_diagnostics_distinguish_large_shift(suite):
    train, _, _ = partitions()
    result = suite.statistical_diagnostics(np.concatenate([train[:10], train[:10] + 50]))
    assert np.mean(result['mahalanobis_squared'][10:]) > np.mean(result['mahalanobis_squared'][:10]) * 100
    assert result['sequential'][-1]['change_candidate']
    assert result['sequential'][-1]['ewma'] > result['sequential'][0]['ewma'] * 10


def test_cusum_does_not_accumulate_alternating_zero_mean_excursions(suite):
    # Alternating +/- 1 standardized deviation has no persistent signed shift.
    robust = np.tile([1., -1.], 50)[:, None] * np.ones((1, len(FEATURES)))
    scaled = suite.median + robust * suite.mad
    values = suite.scaler.inverse_transform(scaled)
    result = suite.statistical_diagnostics(values)['sequential']
    assert max(r['cusum'] for r in result) <= .5 + 1e-10
    assert not any(r['change_candidate'] for r in result)

