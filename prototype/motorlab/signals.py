"""Deterministic fixtures, strict raw-data gate and physically scoped DSP.

Arrays are sample-major, with three currents followed by three voltages.
Timestamps use integer microseconds. No missing samples are interpolated.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import csv
import numpy as np
from scipy import signal, stats
from .contracts import CHANNELS, UNITS, FEATURE_SCHEMA, SCENARIOS, SensorContract, WindowConfig, FilterConfig


def synthesize(scenario='healthy', seconds=1, seed=42, fs=10000, load=1.0,
               frequency=50.0, motor_id='SIM-01'):
    if scenario not in SCENARIOS:
        raise ValueError(f'Unknown scenario: {scenario}')
    if seconds <= 0 or fs <= 0 or not 0 < frequency < fs / 2 or load < 0:
        raise ValueError('Invalid signal parameters')
    if 1_000_000 % fs:
        raise ValueError('Integer-microsecond grid requires sample rate dividing 1e6')
    n = int(round(seconds * fs))
    t = np.arange(n) / fs
    rng = np.random.default_rng(seed)
    angle = 2 * np.pi * frequency * t[:, None] - np.arange(3)[None, :] * 2 * np.pi / 3
    envelope = np.full((n, 1), load)
    if scenario == 'load_variation':
        envelope *= 1 + .15 * np.sin(2 * np.pi * .4 * t[:, None])
    elif scenario == 'startup':
        envelope *= 1 + 4 * np.exp(-t[:, None] / .15)
    elif scenario == 'shutdown':
        envelope *= np.maximum(0, 1 - t[:, None] / max(seconds * .75, .01))
    elif scenario in ('degradation', 'combined'):
        envelope *= 1 + .5 * t[:, None] / seconds
    voltage = np.sqrt(2) * 230 * np.sin(angle)
    current = np.sqrt(2) * 10 * envelope * np.sin(angle - np.arccos(.85))
    if scenario in ('voltage_imbalance', 'combined'):
        voltage[:, 0] *= .78
    if scenario == 'current_imbalance':
        current[:, 0] *= 1.5
    if scenario == 'phase_loss':
        current[:, 0] = 0
    if scenario in ('harmonics', 'combined'):
        current += np.sqrt(2) * 2 * np.sin(5 * angle)
        voltage += np.sqrt(2) * 10 * np.sin(5 * angle)
    if scenario == 'transient':
        a = n // 2
        current[a:a + max(1, int(.003 * fs)), 0] += 55
    # Noise deliberately small; the analytic references can use analytic_record.
    current += rng.normal(0, .01, current.shape)
    voltage += rng.normal(0, .03, voltage.shape)
    values = np.column_stack([current, voltage])
    ts = np.arange(n, dtype=np.int64) * (1_000_000 // fs)
    if scenario == 'dropout':
        values[n // 2:n // 2 + max(1, n // 50), 1] = np.nan
    if scenario == 'timestamp_gap':
        ts[n // 2:] += 10 * (1_000_000 // fs)
    meta = SensorContract(sample_rate_hz=fs, motor_id=motor_id).to_dict()
    meta.update(seed=int(seed), scenario=scenario, nominal_frequency_hz=float(frequency),
                load_fraction=float(load), healthy_label=scenario in ('healthy', 'load_variation'),
                operating_state='transition' if scenario in ('startup', 'shutdown') else 'steady',
                simulated_ground_truth=True, phase_mapping_verified=True)
    vib = rng.normal(0, .15, (n, 3))
    temp = 45 + rng.normal(0, .02, n)
    if scenario in ('bearing_wear', 'combined'):
        vib += (1 + 4 * t[:, None] / seconds) * np.sin(2 * np.pi * 120 * t[:, None])
    if scenario in ('thermal', 'combined'):
        temp += 35 * t / seconds
    return {'timestamps': ts, 'values': values, 'metadata': meta,
            'optional': {'vibration': {'values': vib, 'unit': 'm/s2', 'provenance': 'SIMULATED'},
                         'temperature': {'values': temp, 'unit': 'degC', 'provenance': 'SIMULATED'}}}


def validate(record):
    reasons, warnings = [], []
    meta = record.get('metadata', {})
    x = np.asarray(record.get('values', []))
    ts = np.asarray(record.get('timestamps', []))
    fs = meta.get('sample_rate_hz', 0)
    if x.ndim != 2 or x.shape[1:] != (6,):
        reasons.append('CHANNEL_SHAPE')
    if x.dtype.kind not in 'fiu':
        reasons.append('NONNUMERIC')
    if ts.ndim != 1 or len(ts) < 2 or x.ndim != 2 or len(ts) != len(x):
        reasons.append('TIMESTAMP_SHAPE')
    if ts.dtype.kind not in 'iu':
        reasons.append('TIMESTAMP_PRECISION')
    if meta.get('timestamp_unit') != 'us':
        reasons.append('TIMESTAMP_UNIT')
    fs_valid = isinstance(fs, (float, int)) and np.isfinite(fs) and fs > 0
    if not fs_valid:
        reasons.append('SAMPLE_RATE')
    if tuple(meta.get('channels', ())) != CHANNELS:
        reasons.append('CHANNEL_MAPPING')
    if tuple(meta.get('units', ())) != UNITS:
        reasons.append('UNITS')
    if meta.get('provenance') not in ('MEASURED', 'SIMULATED'):
        reasons.append('PROVENANCE')
    if not meta.get('motor_id'):
        reasons.append('MOTOR_ID')
    if not meta.get('scaling_verified'):
        reasons.append('SCALING_UNVERIFIED')
    missing = 0
    if not reasons and len(ts) > 1:
        d = np.diff(ts.astype(np.int64))
        nominal = 1_000_000 / fs
        if np.any(d == 0): reasons.append('DUPLICATE_TIMESTAMP')
        if np.any(d < 0): reasons.append('NON_MONOTONIC')
        if np.any(np.abs(d - nominal) > nominal * .01): reasons.append('IRREGULAR_SAMPLING_OR_GAP')
        missing = int(np.maximum(np.round(d / nominal) - 1, 0).sum())
        if not np.isfinite(x).all(): reasons.append('NONFINITE')
        limits = [meta.get('current_limit_a', 0)] * 3 + [meta.get('voltage_limit_v', 0)] * 3
        if min(limits) <= 0:
            reasons.append('SENSOR_RANGE_UNKNOWN')
        elif np.any(np.abs(x) >= np.asarray(limits)):
            reasons.append('SENSOR_RANGE_OR_CLIPPING')
        # Repeated extrema form rail plateaus, unlike legitimate sampled sine peaks.
        for k in range(6):
            v = x[:, k]
            if np.isfinite(v).all() and np.ptp(v) > 0:
                plateau = np.diff(v) == 0
                at_rail = (v[:-1] == v.min()) | (v[:-1] == v.max())
                if np.mean(plateau & at_rail) > .005:
                    reasons.append('CLIPPING_PLATEAU'); break
        if 'channel_timestamps' in record:
            ct = np.asarray(record['channel_timestamps'])
            if ct.shape != x.shape or not np.all(ct == ts[:, None]):
                reasons.append('CHANNEL_SKEW')
    if not meta.get('phase_mapping_verified'):
        warnings.append('POWER_UNAVAILABLE_PHASE_MAPPING')
    if meta.get('voltage_convention') != 'phase_to_neutral':
        warnings.append('POWER_UNAVAILABLE_VOLTAGE_CONVENTION')
    if len(ts) and fs_valid and len(ts) / fs < .1:
        reasons.append('INSUFFICIENT_WINDOW')
    return {'valid': not reasons, 'status': 'VALID' if not reasons else 'INVALID',
            'reasons': sorted(set(reasons)), 'warnings': warnings, 'samples': len(ts),
            'missing_samples': missing, 'provenance': meta.get('provenance', 'UNKNOWN')}


def windows(record, seconds=1.0, overlap=0.0):
    cfg = WindowConfig(seconds, overlap)
    fs = record['metadata']['sample_rate_hz']
    n = int(round(fs * cfg.seconds)); hop = max(1, int(round(n * (1 - overlap))))
    for start in range(0, len(record['timestamps']) - n + 1, hop):
        end = start + n
        out = {'timestamps': np.asarray(record['timestamps'])[start:end],
               'values': np.asarray(record['values'])[start:end],
               'metadata': dict(record['metadata'], window_seconds=seconds, overlap=overlap), 'optional': {}}
        for key, val in record.get('optional', {}).items():
            out['optional'][key] = dict(val, values=np.asarray(val['values'])[start:end])
        if 'channel_timestamps' in record:
            out['channel_timestamps'] = np.asarray(record['channel_timestamps'])[start:end]
        yield out


def filter_values(values, fs, config=None):
    cfg = asdict(config) if isinstance(config, FilterConfig) else dict(config or {'kind': 'none'})
    x = np.array(values, dtype=float, copy=True)
    kind = cfg.get('kind', 'none')
    cutoff = cfg.get('cutoff_hz', ())
    if kind == 'none': return x
    if kind == 'detrend': return signal.detrend(x, axis=0)
    if kind == 'smooth':
        n = int(cfg.get('smoothing_samples', 5))
        if n < 1 or n % 2 == 0: raise ValueError('Median width must be positive and odd')
        from scipy.ndimage import median_filter
        return median_filter(x, size=(n, 1), mode='nearest')
    if kind == 'notch':
        hz = float(cutoff[0])
        if not 0 < hz < fs / 2: raise ValueError('Notch outside Nyquist range')
        b, a = signal.iirnotch(hz, cfg.get('notch_q', 30), fs)
        return signal.filtfilt(b, a, x, axis=0)
    names = {'lowpass': 'lowpass', 'highpass': 'highpass', 'bandpass': 'bandpass'}
    if kind not in names: raise ValueError('Unknown filter kind')
    if not cutoff or any(not 0 < c < fs / 2 for c in cutoff): raise ValueError('Cutoff outside Nyquist range')
    wn = cutoff if kind == 'bandpass' else cutoff[0]
    sos = signal.butter(cfg.get('order', 4), wn, btype=kind, fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x, axis=0)


def _ratio(a, b):
    return float(a / b) if abs(b) > 1e-12 else None


def extract(record, filter_config=None, frequency_bands=None):
    quality = validate(record)
    meta = dict(record.get('metadata', {}), feature_schema=FEATURE_SCHEMA,
                filter_config=asdict(filter_config) if isinstance(filter_config, FilterConfig) else (filter_config or {'kind': 'none'}))
    out = {'quality': quality, 'features': {}, 'spectrum': {}, 'metadata': meta,
           'mcsa': {'status': 'UNAVAILABLE', 'reason': 'Verified speed/slip and pole count required'}, 'optional_features': {}}
    if not quality['valid']: return out
    x = filter_values(record['values'], meta['sample_rate_hz'], filter_config)
    if meta['filter_config'].get('kind', 'none') != 'none':
        quality['warnings'].append('FILTERED_FEATURES_EDGE_ARTIFACTS_POSSIBLE')
    n, fs = len(x), meta['sample_rate_hz']
    f = np.fft.rfftfreq(n, 1 / fs)
    win = signal.windows.hann(n, sym=False)
    z = np.fft.rfft(x * win[:, None], axis=0)
    amplitude = 2 * np.abs(z) / win.sum()
    amplitude[0] /= 2
    if n % 2 == 0: amplitude[-1] /= 2
    nominal = meta.get('nominal_frequency_hz', 50)
    band = (f >= max(30, nominal - 10)) & (f <= min(80, nominal + 10))
    bins = np.where(band)[0]
    if len(bins) == 0: return dict(out, quality=dict(quality, valid=False, status='INVALID', reasons=['FREQUENCY_UNOBSERVABLE']))
    k = int(bins[np.argmax(np.mean(amplitude[band, 3:], axis=1))])
    fundamental = float(f[k])
    features = {'frequency_hz': fundamental, 'frequency_resolution_hz': float(fs / n), 'samples': n}
    rms = np.sqrt(np.mean(x * x, axis=0))
    harmonics = []
    for h in range(1, min(40, int(fs / 2 / max(fundamental, 1))) + 1):
        kh = int(np.argmin(abs(f - fundamental * h)))
        harmonics.append(amplitude[kh] / np.sqrt(2))
    harmonics = np.asarray(harmonics)
    for group, offset in (('i', 0), ('v', 3)):
        group_thd = []
        for phase in range(3):
            c = phase + offset; s = f'{group}_{phase + 1}'
            features[f'{group}_rms_{phase + 1}'] = float(rms[c])
            features[f'{s}_peak'] = float(np.max(abs(x[:, c])))
            features[f'{s}_crest'] = _ratio(features[f'{s}_peak'], rms[c])
            features[f'{s}_variance'] = float(np.var(x[:, c]))
            features[f'{s}_skewness'] = float(stats.skew(x[:, c])) if np.std(x[:, c]) > 1e-10 else 0.0
            features[f'{s}_kurtosis'] = float(stats.kurtosis(x[:, c], fisher=False)) if np.std(x[:, c]) > 1e-10 else 0.0
            features[f'{s}_transient_step'] = float(np.max(abs(np.diff(x[:, c]))))
            thd = _ratio(np.linalg.norm(harmonics[1:, c]) * 100, harmonics[0, c])
            features[f'{s}_thd_pct'] = thd
            if thd is not None: group_thd.append(thd)
            features[f'{s}_fundamental_phase_deg'] = float(np.angle(z[k, c], deg=True))
        r = rms[offset:offset + 3]
        features[f'{group}_imbalance_pct'] = _ratio(np.max(abs(r - r.mean())) * 100, r.mean())
        features[f'{group}_thd_pct'] = float(np.mean(group_thd)) if group_thd else None
    power_ok = meta.get('phase_mapping_verified') and meta.get('voltage_convention') == 'phase_to_neutral'
    features.update(power_w=None, apparent_power_va=None, reactive_fundamental_var=None, power_factor=None)
    if power_ok:
        p = np.mean(x[:, :3] * x[:, 3:], axis=0)
        apparent = float(np.sum(rms[:3] * rms[3:]))
        phase = np.angle(z[k, 3:]) - np.angle(z[k, :3])
        q = harmonics[0, :3] * harmonics[0, 3:] * np.sin(phase)
        features.update(power_w=float(p.sum()), apparent_power_va=apparent,
                        reactive_fundamental_var=float(q.sum()), power_factor=_ratio(p.sum(), apparent))
        for j in range(3): features[f'power_w_{j + 1}'] = float(p[j])
    # Negative sequence depends on verified phase order.
    for group, offset in (('i', 0), ('v', 3)):
        features[f'{group}_negative_sequence_pct'] = None
        if meta.get('phase_mapping_verified'):
            ph = z[k, offset:offset + 3]
            a = np.exp(2j * np.pi / 3)
            positive = (ph[0] + a * ph[1] + a * a * ph[2]) / 3
            negative = (ph[0] + a * a * ph[1] + a * ph[2]) / 3
            features[f'{group}_negative_sequence_pct'] = _ratio(abs(negative) * 100, abs(positive))
    pf, psd = signal.welch(x, fs=fs, window='hann', nperseg=min(n, 2048), axis=0)
    features['spectral_energy_a2'] = float(np.trapezoid(psd[:, :3].mean(axis=1), pf))
    bands = frequency_bands or {'supply': (40, 70), 'harmonics': (100, 1000)}
    for name, limits in bands.items():
        low, high = limits
        if not 0 <= low < high <= fs / 2:
            raise ValueError('Frequency bands must lie within Nyquist range')
        selected = (pf >= low) & (pf <= high)
        features[f'band_{name}_energy_a2'] = float(np.trapezoid(psd[selected, :3].mean(axis=1), pf[selected]))
    meta['frequency_bands_hz'] = bands
    peaks, _ = signal.find_peaks(amplitude[:, 0], prominence=max(amplitude[:, 0].max() * .01, 1e-9))
    top = sorted(peaks, key=lambda j: amplitude[j, 0], reverse=True)[:12]
    out.update(features=features, spectrum={'frequency_hz': f.tolist(), 'amplitude': amplitude.tolist(),
        'amplitude_units': ['A_peak'] * 3 + ['V_peak'] * 3,
        'psd_frequency_hz': pf.tolist(), 'psd': psd.tolist(), 'window': 'periodic Hann',
        'peaks_hz': [float(f[j]) for j in top], 'harmonic_rms': harmonics.tolist()})
    for name, sensor in record.get('optional', {}).items():
        v = np.asarray(sensor.get('values', []))
        expected = {'vibration': 'm/s2', 'temperature': 'degC'}.get(name)
        if expected is None or sensor.get('unit') != expected or not np.isfinite(v).all() or len(v) != n:
            out['optional_features'][name] = {'status': 'INVALID', 'reason': 'units, length or numeric quality'}
            continue
        out['optional_features'][name] = {'status': 'VALID', 'provenance': sensor.get('provenance', 'UNKNOWN'),
            'unit': expected, 'rms': np.sqrt(np.mean(v * v, axis=0)).tolist(),
            'mean': np.mean(v, axis=0).tolist(), 'max': np.max(v, axis=0).tolist()}
    poles, speed = meta.get('pole_count'), meta.get('rotor_speed_rpm')
    if poles and speed is not None and poles >= 2 and poles % 2 == 0:
        sync = 120 * fundamental / poles
        slip = (sync - speed) / sync
        if 0 <= slip < 1:
            spacing = 2 * slip * fundamental
            out['mcsa'] = {'status': 'EXPLORATORY' if spacing >= 2 * fs / n else 'UNRESOLVED',
                'slip': float(slip), 'sidebands_hz': [fundamental - spacing, fundamental + spacing],
                'reason': 'Candidate rotor sidebands; not a validated fault diagnosis', 'frequency_resolution_hz': fs / n}
            if out['mcsa']['status'] == 'EXPLORATORY':
                sb = [int(np.argmin(abs(f - hz))) for hz in out['mcsa']['sidebands_hz']]
                out['mcsa']['sideband_current_peak_a'] = [float(amplitude[j, :3].mean()) for j in sb]
                denom = float(amplitude[k, :3].mean())
                out['mcsa']['sideband_dbc'] = [float(20 * np.log10(max(amplitude[j, :3].mean(), 1e-15) / max(denom, 1e-15))) for j in sb]
    return out


def read_csv(path, metadata):
    """Strict offline replay. Caller must supply provenance, calibrated units and limits."""
    required = ['timestamp_us', *CHANNELS]
    with Path(path).open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if not all(c in (reader.fieldnames or []) for c in required): raise ValueError(f'Required columns: {required}')
        rows = list(reader)
    try:
        ts = np.array([int(r['timestamp_us']) for r in rows], dtype=np.int64)
    except (ValueError, OverflowError) as exc:
        raise ValueError('timestamp_us must contain integer microseconds') from exc
    result = {'timestamps': ts, 'values': np.array([[float(r[c]) for c in CHANNELS] for r in rows], dtype=float),
              'metadata': dict(metadata, source='offline_csv', file_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())}
    return result


def aggregate(records, seconds=60):
    if seconds not in (10, 60, 300, 900, 3600): raise ValueError('Unsupported aggregation interval')
    groups = {}
    for row in records:
        # Do not pool motors, provenance, regimes, or invalid observations.
        meta = row['metadata']
        key = (meta['motor_id'], meta['provenance'], meta.get('operating_state', 'unknown'), int(row['timestamp_us'] // (seconds * 1e6)))
        groups.setdefault(key, []).append(row)
    out = []
    for key, rows in groups.items():
        good = [r for r in rows if r['quality']['valid']]
        stats_out = {}
        for name in (good[0]['features'] if good else []):
            vals = [r['features'].get(name) for r in good]
            vals = [v for v in vals if v is not None and np.isfinite(v)]
            if vals: stats_out[name] = {'mean': float(np.mean(vals)), 'max': float(np.max(vals)), 'std': float(np.std(vals))}
        out.append({'motor_id': key[0], 'provenance': key[1], 'operating_state': key[2],
            'timestamp_us': int(key[3] * seconds * 1e6), 'period_seconds': seconds,
            'valid_windows': len(good), 'invalid_windows': len(rows) - len(good), 'features': stats_out})
    return out
