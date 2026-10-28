import copy
import csv
import numpy as np
import pytest
from motorlab.signals import synthesize, validate, extract, windows, filter_values, read_csv, aggregate
from motorlab.contracts import CHANNELS, WINDOW_SECONDS


def analytical(frequency=50, seconds=1, pf=.8):
    rec = synthesize(seconds=seconds, frequency=frequency)
    t = rec['timestamps'] / 1e6
    angle = 2 * np.pi * frequency * t[:, None] - np.arange(3)[None, :] * 2 * np.pi / 3
    rec['values'] = np.column_stack([np.sqrt(2) * 10 * np.sin(angle - np.arccos(pf)), np.sqrt(2) * 230 * np.sin(angle)])
    return rec


@pytest.mark.parametrize('frequency', [50, 60])
@pytest.mark.parametrize('seconds', WINDOW_SECONDS)
def test_analytic_rms_frequency_power(frequency, seconds):
    row = extract(analytical(frequency, seconds))
    f = row['features']
    assert row['quality']['valid']
    assert f['i_rms_1'] == pytest.approx(10, rel=1e-10)
    assert f['v_rms_1'] == pytest.approx(230, rel=1e-10)
    assert f['power_w'] == pytest.approx(3 * 230 * 10 * .8, rel=1e-10)
    assert f['power_factor'] == pytest.approx(.8, abs=1e-10)
    assert f['reactive_fundamental_var'] == pytest.approx(3 * 230 * 10 * .6, rel=1e-8)
    assert f['frequency_hz'] == pytest.approx(frequency)
    assert f['frequency_resolution_hz'] == pytest.approx(1 / seconds)
    assert f['i_thd_pct'] < 1e-8


def test_harmonics_calibrated_amplitude():
    rec = analytical()
    t = rec['timestamps'] / 1e6
    rec['values'][:, 0] += np.sqrt(2) * 2 * np.sin(2 * np.pi * 250 * t)
    assert extract(rec)['features']['i_1_thd_pct'] == pytest.approx(20, abs=1e-7)


@pytest.mark.parametrize('mutation,reason', [
    ('duplicate', 'DUPLICATE_TIMESTAMP'), ('backward', 'NON_MONOTONIC'),
    ('gap', 'IRREGULAR_SAMPLING_OR_GAP'), ('nan', 'NONFINITE'),
    ('unit', 'UNITS'), ('skew', 'CHANNEL_SKEW'), ('clip', 'SENSOR_RANGE_OR_CLIPPING')])
def test_quality_rejects(mutation, reason):
    rec = analytical()
    if mutation == 'duplicate': rec['timestamps'][100] = rec['timestamps'][99]
    if mutation == 'backward': rec['timestamps'][100] = 0
    if mutation == 'gap': rec['timestamps'][100:] += 100
    if mutation == 'nan': rec['values'][100, 0] = np.nan
    if mutation == 'unit': rec['metadata']['units'] = ['mA'] * 6
    if mutation == 'skew':
        rec['channel_timestamps'] = np.tile(rec['timestamps'][:, None], (1, 6))
        rec['channel_timestamps'][:, 2] += 100
    if mutation == 'clip': rec['values'][100, 0] = 100
    assert reason in validate(rec)['reasons']
    assert extract(rec)['features'] == {}


def test_power_gated_and_phase_order():
    rec = analytical()
    rec['metadata']['voltage_convention'] = 'line_to_line'
    assert extract(rec)['features']['power_w'] is None
    rec = analytical()
    rec['metadata']['phase_mapping_verified'] = False
    assert extract(rec)['features']['power_factor'] is None
    rec = analytical()
    rec['values'][:, [1, 2]] = rec['values'][:, [2, 1]]
    # Reversed sequence produces vanishing positive sequence and cannot yield a finite ratio.
    assert extract(rec)['features']['i_negative_sequence_pct'] is None or extract(rec)['features']['i_negative_sequence_pct'] > 1e5


def test_filters_preserve_original_and_suppress_high_tone():
    rec = analytical()
    t = rec['timestamps'] / 1e6
    rec['values'][:, 0] += 5 * np.sin(2 * np.pi * 1500 * t)
    original = rec['values'].copy()
    filtered = filter_values(original, 10000, {'kind': 'lowpass', 'cutoff_hz': [200]})
    baseline = analytical()['values']
    assert np.std(filtered[300:-300, 0] - baseline[300:-300, 0]) < .01
    assert np.array_equal(rec['values'], original)
    with pytest.raises(ValueError): filter_values(original, 10000, {'kind': 'lowpass', 'cutoff_hz': [6000]})


def test_window_alignment_no_gap_fill():
    rec = synthesize(seconds=2)
    chunks = list(windows(rec, 1, .5))
    assert len(chunks) == 3
    assert chunks[1]['timestamps'][0] == 500000
    assert chunks[-1]['timestamps'][-1] == 1999900
    rec = synthesize(scenario='timestamp_gap', seconds=2)
    assert not all(validate(c)['valid'] for c in windows(rec, 1, .5))


def test_replay_preserves_values_and_requires_contract(tmp_path):
    rec = analytical()
    p = tmp_path / 'fixture.csv'
    with p.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['timestamp_us', *CHANNELS])
        writer.writerows([int(t), *v] for t, v in zip(rec['timestamps'], rec['values']))
    replay = read_csv(p, rec['metadata'])
    assert validate(replay)['valid']
    assert np.allclose(replay['values'], rec['values'])
    assert len(replay['metadata']['file_sha256']) == 64
    replay['metadata']['units'] = []
    assert not validate(replay)['valid']


def test_optional_sensor_units_and_mcsa_gate():
    rec = analytical()
    assert extract(rec)['mcsa']['status'] == 'UNAVAILABLE'
    rec['metadata'].update(pole_count=4, rotor_speed_rpm=1440)
    assert extract(rec)['mcsa']['sidebands_hz'] == pytest.approx([46, 54])
    rec['optional']['vibration']['unit'] = 'Hz'
    assert extract(rec)['optional_features']['vibration']['status'] == 'INVALID'


def test_determinism_and_invalid_scenarios():
    a, b = synthesize(seed=123), synthesize(seed=123)
    assert np.array_equal(a['values'], b['values'])
    assert not validate(synthesize('dropout'))['valid']
    assert not validate(synthesize('timestamp_gap'))['valid']
    with pytest.raises(ValueError): synthesize('invented')


def test_aggregate_quality_and_motor_separation():
    a = extract(synthesize()); a['timestamp_us'] = 0
    b = extract(synthesize('dropout')); b['timestamp_us'] = 1_000_000
    c = extract(synthesize(motor_id='SIM-02')); c['timestamp_us'] = 0
    result = aggregate([a, b, c], 10)
    assert len(result) == 2
    assert result[0]['valid_windows'] == 1
    assert result[0]['invalid_windows'] == 1

