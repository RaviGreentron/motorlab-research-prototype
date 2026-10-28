# Feature catalog

Schema: `motorlab.features/1`; implementation: `motorlab/signals.py`. A missing numerical result is null, never a healthy zero.

| Family | Representative keys | Unit and interpretation |
|---|---|---|
| RMS | `i_rms_1..3`, `v_rms_1..3` | A, V; per-phase energy-equivalent amplitude |
| Imbalance | `i_imbalance_pct`, `v_imbalance_pct` | % maximum RMS deviation from phase mean |
| Waveform descriptors | `i_1_peak`, `i_1_crest`, variance, skewness, kurtosis, transient step; same for all channels | Peak A/V, dimensionless shape, variance squared units, maximum adjacent sample change |
| Supply | `frequency_hz`, `frequency_resolution_hz`, `samples` | Hz and count |
| Harmonics | `i_1_thd_pct` etc., `i_thd_pct`, `v_thd_pct` | % through up to harmonic 40; nearest-bin limitation |
| Phase | `i_1_fundamental_phase_deg` etc. | FFT phase degrees, relative to record start |
| Sequences | `i_negative_sequence_pct`, `v_negative_sequence_pct` | % negative/positive fundamental sequence, phase mapping gated |
| Power | `power_w`, `power_w_1..3`, `apparent_power_va`, `reactive_fundamental_var`, `power_factor` | W, VA, fundamental var, unitless; wiring gated |
| Spectral | `spectral_energy_a2`, configured band energy | Mean current PSD integral, A² |
| Optional sensors | vibration/temperature rms, mean, max | m/s² or °C, separate provenance and validity |

Anomaly training currently uses eleven features: three current RMS, three voltage RMS, current/voltage imbalance, current/voltage THD and power factor. Additional calculated features are available for inspection but are not silently included in fitting.

The spectrum result includes frequency bins, six-channel peak amplitudes, Welch PSD, harmonic RMS arrays and largest phase-1 current peaks. Exploratory MCSA results include expected sideband frequencies and, when resolvable, current amplitudes/dBc. They do not identify a confirmed rotor defect.

Aggregation supports 10/60/300/900/3600 seconds, retaining mean/max/std, valid/invalid counts and separation by motor, provenance and regime. Sparse coverage does not become a complete hour of evidence merely because an hourly bucket exists.
