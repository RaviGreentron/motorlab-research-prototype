"""Versioned, explicit contracts for isolated motor research."""
from dataclasses import dataclass, field, asdict
from typing import Literal

CHANNELS = tuple([f'ac_current_{i}' for i in range(1, 4)] + [f'ac_volt_{i}' for i in range(1, 4)])
UNITS = ('A', 'A', 'A', 'V', 'V', 'V')
FEATURE_SCHEMA = 'motorlab.features/1'
WINDOW_SECONDS = (0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
SCENARIOS = ('healthy', 'load_variation', 'startup', 'shutdown', 'voltage_imbalance',
             'current_imbalance', 'phase_loss', 'harmonics', 'transient', 'dropout',
             'timestamp_gap', 'degradation', 'bearing_wear', 'thermal', 'combined')


@dataclass(frozen=True)
class SensorContract:
    sample_rate_hz: int = 10000
    channels: tuple = CHANNELS
    units: tuple = UNITS
    provenance: Literal['SIMULATED', 'MEASURED'] = 'SIMULATED'
    voltage_convention: str = 'phase_to_neutral'
    phase_mapping_verified: bool = True
    scaling_verified: bool = True
    timestamp_unit: str = 'us'
    motor_id: str = 'SIM-01'
    current_limit_a: float = 100.0
    voltage_limit_v: float = 1000.0
    source: str = 'analytical_simulation'
    operating_state: str = 'steady'

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class WindowConfig:
    seconds: float = 1.0
    overlap: float = 0.0

    def __post_init__(self):
        if self.seconds not in WINDOW_SECONDS:
            raise ValueError(f'Window seconds must be one of {WINDOW_SECONDS}')
        if not 0 <= self.overlap < 1:
            raise ValueError('Overlap must be in [0,1)')


@dataclass(frozen=True)
class FilterConfig:
    kind: str = 'none'
    cutoff_hz: tuple = field(default_factory=tuple)
    order: int = 4
    notch_q: float = 30.0
    smoothing_samples: int = 5

