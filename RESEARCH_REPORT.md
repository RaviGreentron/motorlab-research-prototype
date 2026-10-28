# MotorLab — consolidated research assessment

Delivered 27 October 2026. **Local prototype implemented and tested; real-motor suitability remains INCONCLUSIVE.**

## Delivered

- React/TypeScript dashboard and loopback FastAPI backend, with eight views, immutable study creation, selected waveform inspection, persistent annotations and JSON export.
- Six-channel 10 kHz simulation, strict CSV replay, quality validation, windowing, filters, RMS/power/harmonics/FFT/Welch, sensor provenance and aggregate features.
- Four model tracks: robust statistical detection, scikit-learn Isolation Forest, CPU NumPy autoencoder, and classical forecasting.
- Evidence-based fault hypotheses, experimental health index, persistence, multisensor demonstration and advisory inspection recommendations.
- A separate, explicitly synthetic threshold-crossing RUL experiment. Real-motor RUL remains disabled.
- Versioned run reports, data/source hashes, training histories, model checkpoints, dependency locks, tests and technical documentation.

## Verification evidence

67 pytest checks passed, with one upstream TestClient deprecation warning. TypeScript checking and Vite production build passed. Fifteen browser workflow checks and five focused display/units checks passed; no browser JavaScript errors were recorded. Screenshots were visually inspected. See `data/pytest-results.xml`, `data/qa/e2e-results.json` and `data/qa/forecast-e2e-results.json`.

Seven benchmark studies evaluated 0.1/0.2/0.5/1/2/5-second windows with seed 42, plus a second seed at one second. Each study generated 720 windows across three simulated motors; 180 test windows were scored after excluding data-quality failures and transitions. SIM-03 was held out from fitting/calibration; its baseline used SIM-01/02. A separate same-seed repeat matched raw hashes and detection metrics exactly.

## One-second reference results

Reference run: `20261027T110913-88948278`. Repeat run: `20261027T111026-2dedac65`. These are synthetic scenario results, not industrial acceptance evidence.

| Detector | Precision | Recall | F1 | False-positive rate |
|---|---:|---:|---:|---:|
| Robust statistics | 0.854 | 1.000 | 0.921 | 24.0% |
| Isolation Forest | 0.851 | 0.762 | 0.804 | 18.7% |
| Autoencoder | 0.840 | 1.000 | 0.913 | 26.7% |

The negative set contains only 75 scored windows per study. Normal load variation creates false alarms. Isolation Forest trades lower false positives for missed anomalous windows; neither ML model establishes an overall advantage. Do not select a production model or optimal window from these fixtures.

| Window (s) | DSP p95 (ms) | A F1 | B F1 | C F1 |
|---:|---:|---:|---:|---:|
| 0.1 | 3.84 | 0.913 | 0.832 | 0.925 |
| 0.2 | 5.40 | 0.905 | 0.785 | 0.933 |
| 0.5 | 6.94 | 0.909 | 0.738 | 0.921 |
| 1 | 10.90 | 0.921 | 0.804 | 0.913 |
| 2 | 22.07 | 0.929 | 0.812 | 0.929 |
| 5 | 58.89 | 0.929 | 0.843 | 0.917 |

These timings measure extraction after in-memory generation on this machine. They exclude production ingestion, storage/network bottlenecks and continuous operational load. Window-duration changes also change within-window scenarios, so this is not a controlled optimization study.

## Forecast and RUL findings

Forecasting used an independent simulated temperature trajectory at one-minute cadence, with 16 rolling origins and five-step horizons. The first four origins initialize interval calibration; coverage uses the remaining 12 origins. It is separate from selected motor waveform history.

| Forecast | MAE (°C) | RMSE (°C) | 90% interval coverage |
|---|---:|---:|---:|
| naive | 0.5490 | 0.6304 | 50.0% |
| linear | 1.0202 | 1.1606 | 3.3% |
| robust | 1.4524 | 1.6631 | 1.7% |
| holt | 0.1028 | 0.1274 | 86.7% |

The separate quadratic toy RUL test had MAE 1.0 one-minute steps and 100% interval coverage across four origins. It assumes the simulator's functional form and arbitrary 70 °C endpoint; this is not motor failure prediction. Poor interval coverage in some classical forecasts is retained in the evidence, not hidden.

## Limitations and unfinished requirements

- No measured motor performance, validated failure histories, physical sensor installation, or production InfluxDB authorization was established. Real RUL, service dates, and industrial acceptance remain blocked.
- Foundation-model runtimes were not installed or benchmarked. Chronos/TimesFM feasibility is documented; this deliverable provides no evidence that either improves motor forecasting. Model/version/license selection and an appropriate dataset remain separate work.
- Autoencoder is a compact CPU NumPy implementation; PyTorch/GPU compatibility and sequence autoencoders were not implemented.
- Multisensor fusion uses illustrative optional-sensor thresholds, not validated industrial calibration. Health/severity and diagnosis rules remain experimental.
- CSV replay provides quality-gated features, not an approved measured-data training workflow. InfluxDB is explicitly unavailable; no live adapter is represented as operational.
- Sequential statistical diagnostics use filtered per-regime rows and are not a gap-aware production stream monitor. MCSA reports candidate frequencies/eligibility; it does not validate rotor or bearing faults.
- FFT harmonic estimates are finite-window bin estimates; non-bin-centred supply frequencies, aliasing and actual sensor calibration need deeper physical validation.
- Scenario-block event metrics and per-motor-day extrapolations from tiny exposure are descriptive only. They are not operational false-alarm estimates.
- No plant control, work-order automation, external alerts or production deployment is included.

## Recommendation

**GO for further controlled research; REVISE load/regime handling; NO-GO for operational maintenance decisions.** Next, obtain a verified read-only export with phase convention, units/scaling, sensor limits, load/speed context and independent healthy/fault labels. Freeze a prospective acceptance protocol, improve normal-load robustness, and evaluate unseen measured motors before enabling real prognosis.

## Launch and files

Use `prototype/start.ps1` and open http://127.0.0.1:8765. See `START_HERE.md` for setup, rerun and replay instructions. Documentation is outside source in `docs`; runs and models are in `data`. The original D-drive project and production data were not modified.

## Research references

[xPump overview](https://www.einnosys.com/xpump/) and [industrial guide](https://www.einnosys.com/ai-motor-predictive-maintenance-industrial-guide/) informed product concepts only. Proprietary vendor methods and performance were not reproduced or verified. [Chronos repository](https://github.com/amazon-science/chronos-forecasting) and [TimesFM repository](https://github.com/google-research/timesfm) were reviewed for optional forecasting research. See MODEL_D_FORECASTING.md for license and feasibility limits.
