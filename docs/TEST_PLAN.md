# Verification plan and executed scope

Status at delivery: **67 pytest tests passed**, recorded in `outputs/data/pytest-results.xml`. Browser evidence comprises 15 workflow checks plus five focused checks for final UI corrections; use the saved browser result files and final report for their exact scope. These counts are not industrial acceptance claims.

| Gate | Executed checks | Boundary |
|---|---|---|
| Signal correctness | 50/60 Hz analytic RMS, active/reactive power, power factor, six window lengths, harmonic amplitude, filters, phase gating | Bin-centered analytical references; no sensor calibration laboratory |
| Quality | Duplicate/backward timestamps, gaps, NaNs, units, skew, clipping, invalid windows | Synthetic fixtures, not verified field acquisition |
| Models | Training-only scaling, calibration isolation, deterministic AE learning, best checkpoint, IF large-shift response, serialization, signed CUSUM | Does not establish general industrial anomaly accuracy |
| Intelligence | Severe single-signal evidence, missing sensors, persistence/hysteresis, invalid score, unknown cause, unavailable RUL | Illustrative thresholds |
| Forecast | Analytic linear trend, chronological fitting, horizon metrics, coverage denominators, disjoint backtests | Synthetic temperature, empirical intervals |
| Replay and toy RUL | CSV/overlap behavior and explicit simulator crossing tests | No measured baseline or real RUL validation |
| API | Input bounds, no production source, origin restrictions, not-found state, waveform consistency, notes and export | Local service only |
| Browser | Study creation, navigation, selected waveform, rejected spectrum, annotation persistence, export and responsive layout; focused corrections | A bounded workflow suite, not complete accessibility/load coverage |

The research validation runner executed six window lengths with seed 42, one 1-second study with seed 7, and a repeated seed-42 1-second study. Raw hash and detection metrics reproduced exactly. It also evaluated toy threshold crossing at four origins. Evidence: `outputs/data/validation-summary.json`.

PASS means executed and assertions satisfied. FAIL means executed and unmet. SKIPPED means intentionally omitted by a test mechanism. BLOCKED describes unavailable authorized data/access. NOT RUN describes an unexecuted experiment such as foundation-model comparison. Live Influx, prospective field evaluation, measured fault diagnosis and GPU testing are not passed tests.
