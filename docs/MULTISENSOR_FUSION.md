# Multisensor fusion

The current fusion is an explicitly experimental maximum-evidence rule. The electrical input is the largest A/B/C threshold ratio. Simulated vibration contributes maximum axis RMS divided by 0.5 m/s². Simulated temperature contributes max(0,(mean temperature−45°C)/10°C). The sensor scale constants are illustrative and **not calibrated industrial thresholds**.

The maximum available score preserves severe evidence from one sensor even if the others are quiet. A score at least 3 maps to CRITICAL; above 1 maps to WARNING; otherwise NORMAL. Available and missing groups are retained. No usable groups yields UNASSESSABLE with a null score. More than one above-threshold group is described as correlated evidence; this does not establish statistical causality or a unique physical fault.

Persistence requires two successive above-1 observations, releases below 0.8 and immediately accepts a severe score of at least 3. Invalid/nonfinite windows reset state. The study additionally makes invalid electrical windows and startup/shutdown windows unassessable; optional sensor values do not override that study-level eligibility gate.

Fusion metrics use a broader positive set than electrical-only detector metrics: simulated bearing-wear and thermal scenarios are positives for fusion but electrical negatives for A/B/C. Their precision/recall therefore do not constitute a controlled same-target ablation showing that sensor fusion improves performance.

Tests cover missing evidence, severe single-signal preservation, correlated flags, hysteresis and invalid-window reset. Weighted/statistical learned fusion, optimized thresholds, sensor reliability models and measured multimodal validation remain unimplemented.
