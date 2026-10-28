import numpy as np
import pytest
from motorlab.intelligence import persistent_alerts, fuse, diagnose, rul_eligibility
from motorlab.forecast import predict, backtest


def test_persistence_hysteresis_and_severe_single_sample():
    result = persistent_alerts([.3, 1.2, .4, 1.1, 1.2, .9, .7, 3.1, .5])
    assert result.tolist() == [False, False, False, False, True, True, False, True, False]


def test_invalid_window_resets_alert_streak():
    result = persistent_alerts([1.2, 4., 1.2, 1.2], valid=[True, False, True, True])
    assert result.tolist() == [False, False, False, True]
    assert not persistent_alerts([np.nan, np.inf, .4]).any()


def test_fusion_missing_data_and_severe_evidence():
    missing = fuse({'electrical': None, 'thermal': np.nan, 'vibration': None})
    assert missing['status'] == 'UNASSESSABLE'
    assert missing['score'] is None
    severe = fuse({'electrical': 4., 'thermal': .1, 'vibration': None})
    assert severe['status'] == 'CRITICAL'
    assert severe['score'] == 4
    assert severe['missing'] == ['vibration']
    assert fuse({'electrical': 1.3, 'thermal': 1.7})['pattern'] == 'correlated'


def test_diagnosis_never_invents_bearing_cause_or_rul():
    unknown = diagnose({'i_rms_1': 10., 'i_rms_2': 10., 'i_rms_3': 10.}, 2.)
    assert unknown['status'] == 'ANOMALY_DETECTED_CAUSE_UNKNOWN'
    assert unknown['hypotheses'] == []
    assert unknown['rul_status'] == 'RUL_NOT_ESTIMABLE'
    assert unknown['service_window'] is None
    rejected = diagnose({}, 5., quality=False)
    assert rejected['health_index'] is None
    assert rejected['status'] == 'UNASSESSABLE'


@pytest.mark.parametrize('ratio', [None, np.nan, np.inf])
def test_invalid_score_fails_closed(ratio):
    result = diagnose({'v_imbalance_pct': None}, ratio)
    assert result['status'] == 'UNASSESSABLE'
    assert result['health_index'] is None


def test_missing_phase_measurement_is_not_zero_current_evidence():
    result = diagnose({'i_rms_1': 10, 'i_rms_2': None, 'i_rms_3': 10}, 1.5)
    assert not any(h['category'] == 'Phase loss or sensor fault' for h in result['hypotheses'])
    assert result['status'] == 'ANOMALY_DETECTED_CAUSE_UNKNOWN'


def test_diagnosis_evidence_and_severity():
    evidence = diagnose({'v_imbalance_pct': 12., 'i_rms_1': .01, 'i_rms_2': 10., 'i_rms_3': 10.}, 4.)
    categories = [h['category'] for h in evidence['hypotheses']]
    assert 'Voltage imbalance' in categories
    assert 'Phase loss or sensor fault' in categories
    assert evidence['recommendation'] == 'Urgent engineering review'
    assert 'not remaining life' in evidence['health_label']
    for hypothesis in evidence['hypotheses']:
        assert hypothesis['supporting_features']
        assert hypothesis['limitations']


def test_rul_requires_endpoint_histories_and_validation():
    assert rul_eligibility('MEASURED')['status'] == 'RUL_NOT_ESTIMABLE'
    assert rul_eligibility('MEASURED', 'failure', 2, True)['status'] == 'RUL_NOT_ESTIMABLE'
    assert rul_eligibility('MEASURED', 'failure', 10, False)['status'] == 'RUL_NOT_ESTIMABLE'
    eligible = rul_eligibility('SIMULATED', 'defined synthetic failure', 4, True)
    assert eligible['status'] == 'ELIGIBLE_FOR_RESEARCH'
    assert eligible['provenance'] == 'SIMULATED'


@pytest.mark.parametrize('method', ['linear', 'robust', 'holt'])
def test_forecast_linear_reference(method):
    y = 2. + np.arange(60) * .25
    forecast = predict(y, 5, method)
    np.testing.assert_allclose(forecast, 2 + np.arange(60, 65) * .25, atol=.03)


def test_rolling_origin_error_denominators_and_coverage():
    y = 2 + np.arange(80) * .25
    result = backtest(y, horizon=4, initial=40, step=4)
    naive = result['naive']
    assert naive['origins'] == list(range(40, 77, 4))
    assert naive['coverage_origins'] == 6
    assert naive['mae'] == pytest.approx(.625)
    assert naive['bias'] == pytest.approx(-.625)
    np.testing.assert_allclose(naive['mae_by_horizon'], [.25, .5, .75, 1.])
    assert naive['interval_coverage'] == pytest.approx(1.)
    assert result['linear']['mae'] < 1e-9
    assert len(naive['lower']) == 4
    assert np.all(np.array(naive['lower']) <= naive['forecast'])
    assert np.all(np.array(naive['upper']) >= naive['forecast'])
    assert naive['rul_status'] == 'RUL_NOT_ESTIMABLE'


def test_future_values_not_passed_to_origin_fit(monkeypatch):
    import motorlab.forecast as module
    real_predict = module.predict
    calls = []
    y = np.arange(64, dtype=float)
    def spy(history, horizon, method):
        history = np.asarray(history)
        calls.append((history.copy(), method))
        return real_predict(history, horizon, method)
    monkeypatch.setattr(module, 'predict', spy)
    result = module.backtest(y, horizon=4, initial=40, step=4)
    for history, method in calls:
        np.testing.assert_array_equal(history, y[:len(history)])
        assert len(history) in result[method]['origins'] + [len(y)]
    for method in result:
        assert [len(history) for history, name in calls if name == method] == result[method]['origins'] + [len(y)]


def test_training_prefix_prediction_unchanged_by_future_perturbation():
    y = np.sin(np.arange(100) / 15.) + np.arange(100) * .01
    changed = y.copy(); changed[60:] += 1000
    for method in ('naive', 'linear', 'robust', 'holt'):
        np.testing.assert_array_equal(predict(y[:60], 5, method), predict(changed[:60], 5, method))


def test_forecast_rejects_insufficient_or_invalid_input():
    with pytest.raises(ValueError): predict([1, 2, 3], 2, 'naive')
    with pytest.raises(ValueError): predict([1] * 8 + [np.nan], 2, 'linear')
    with pytest.raises(ValueError): backtest(np.arange(20.), initial=40)
    # Earlier-origin residuals would include future outcomes if origins overlap.
    with pytest.raises(ValueError): backtest(np.arange(100.), horizon=5, step=1)

