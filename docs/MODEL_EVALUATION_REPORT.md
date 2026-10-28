# Model evaluation — actual synthetic evidence

Evidence: `outputs/data/validation-summary.json`. Reference run `20261027T110913-88948278`, seed 42, 1-second windows; equivalent repeated run `20261027T111026-2dedac65`. Raw waveform hash and detection metrics matched exactly on repeat. Timing and run IDs are intentionally not expected to match.

Each study generates 240 disjoint windows for each of three simulated motors. Per-motor partitions are train [0,80), early stopping [80,120), calibration [120,160), test [160,240). Light/full regimes alternate. SIM-03 is wholly excluded from fit/calibration and uses pooled SIM-01/02 baselines. Invalid dropout/gap and transition windows remove 60 of the 240 test windows, leaving 180 scored electrical windows: 105 positives and 75 negatives. This is short generator-based evidence, not diverse real-motor validation.

## Reference electrical comparison
| Model | Precision | Recall | F1 | False-positive rate | TP / FP / TN / FN |
|---|---:|---:|---:|---:|---|
| A statistics | 85.37% | 100% | 0.9211 | 24.00% | 105 / 18 / 57 / 0 |
| B Isolation Forest | 85.11% | 76.19% | 0.8040 | 18.67% | 80 / 14 / 61 / 25 |
| C autoencoder | 84.00% | 100% | 0.9130 | 26.67% | 105 / 20 / 55 / 0 |

A and C detect injected abnormalities but have substantial negative-window false alarms. B misses 25 positive windows. A 100% scenario-block event recall for B means at least one hit per block, not detection of every abnormal window. No method is promoted to industrial use.

## Window sensitivity, seed 42
| Seconds | A F1 / FPR | B F1 / FPR | C F1 / FPR |
|---:|---|---|---|
| 0.1 | 0.9130 / 26.67% | 0.8316 / 8.00% | 0.9251 / 22.67% |
| 0.2 | 0.9052 / 29.33% | 0.7853 / 14.67% | 0.9333 / 20.00% |
| 0.5 | 0.9091 / 28.00% | 0.7380 / 17.33% | 0.9211 / 24.00% |
| 1 | 0.9211 / 24.00% | 0.8040 / 18.67% | 0.9130 / 26.67% |
| 2 | 0.9292 / 21.33% | 0.8125 / 12.00% | 0.9292 / 21.33% |
| 5 | 0.9292 / 21.33% | 0.8432 / 2.67% | 0.9170 / 25.33% |

At seed 7, 1-second F1 is A 0.9211, B 0.7839, C 0.9251. Two seeds do not characterize uncertainty across operating populations. Window changes also change simulated event duration; this is not a controlled fixed-duration real-signal replay comparison.

## Forecasts on independent simulated temperature
| Method | MAE °C | RMSE °C | Bias °C | Empirical 90% interval coverage |
|---|---:|---:|---:|---:|
| Naive | 0.5490 | 0.6304 | −0.5447 | 50.00% |
| Linear | 1.0202 | 1.1606 | −1.0202 | 3.33% |
| Robust | 1.4524 | 1.6631 | −1.4524 | 1.67% |
| Holt | 0.1028 | 0.1274 | −0.0625 | 86.67% |

Coverage uses 12 origins × 5 horizons after four calibration origins. Holt is strongest on this chosen accelerating synthetic series; its observed coverage is below nominal. Linear/robust fits markedly underforecast, and intervals fail under nonstationarity.

False-event fields count false-positive window runs within scenario blocks, not operational incidents. At the reference setting A/B/C have 6/5/8 such runs across only 75 negative seconds. Per-motor-day extrapolations (6912/5760/9216) are unstable and not field rates. Window-level Wilson intervals ignore within-event dependence. Fusion uses a different positive set and uncalibrated sensor scales, so it is not a controlled A/B/C improvement claim.
