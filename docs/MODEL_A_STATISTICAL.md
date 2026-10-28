# Model A — statistical baseline

The study fits a `StandardScaler` on healthy training rows only, separately for light/full operating regimes. Within each scaled training set it stores median and MAD; scaled MAD has a 0.05 floor to avoid numerical explosion on almost constant synthetic channels. The anomaly score is the maximum absolute robust z-score across the eleven configured features.

Alert threshold is the 99th percentile of a distinct healthy calibration partition, with a small positive numerical floor. This is an experiment setting, not an approved industrial limit. A threshold ratio above 1 creates a candidate. It is not a failure probability. The floor and max-over-features score affect sensitivity and need validation on real acquisition noise and operating variation.

Additional diagnostics include classical standardized deviations, Ledoit–Wolf shrinkage Mahalanobis squared distance, EWMA with alpha 0.2 and signed two-sided CUSUM with reference 0.5 and illustrative candidate boundary 8. These diagnostics are displayed separately; they do not silently replace the calibrated primary score. Sequential diagnostics are compressed by selected regime in the study and are exploratory rather than a fully continuous online monitoring state machine.

Tests establish train-only scaling, calibration isolation, extreme-shift response and absence of artificial accumulation for alternating zero-mean CUSUM excursions. Real healthy-state segmentation, threshold stability and drift adaptation remain unvalidated. Model contributors are the three largest robust deviations; they describe evidence rather than causal explanations.

See MODEL_EVALUATION_REPORT.md for actual held-out metrics, including false alarms under normal load variation. Do not promote this baseline solely because analytical waveform tests passed.
