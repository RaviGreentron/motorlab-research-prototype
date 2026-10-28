# Model B — Isolation Forest

Implementation uses scikit-learn `IsolationForest` with 150 estimators, `contamination='auto'`, a recorded seed and one worker. Inputs are the same eleven features and training-only scaling used by Model A. Training uses designated healthy rows only. The raw anomaly score is negative `score_samples`; the separate calibration partition sets its 99th-percentile alert threshold.

The estimator's built-in contamination offset does not determine the exported alert; external calibration does. No hyperparameter search or contamination optimization is claimed. Threshold ratios and raw scores are not calibrated fault probabilities.

Within-motor evaluation fits separate light/full baselines. Entire SIM-03 is excluded from fitting and calibration; its study uses pooled SIM-01/02 donors by regime. This checks one synthetic cross-asset transfer case, not population generalization. Synthetic assets share the generator's assumptions.

Tests compare identical training and scoring outputs when only calibration values change, exercise strong out-of-distribution shifts and verify trusted local serialization round trips. Descriptive robust-z contributors are not Isolation Forest feature attribution.

Measured inference/training costs, precision, recall, F1 and false-positive rates reside in the immutable report and validation summary. Any recommendation must consider false alarms, missed scenarios, exposure duration and dataset limitations rather than a single headline metric.
