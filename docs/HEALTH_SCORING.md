# Experimental health index

The displayed index is `clip(100 − 25 × max(0, ratio − 0.5), 0, 100)`, where ratio is the experimental fused evidence score. It is a monotonic visual mapping of deviation, **not percent remaining life, calibrated failure probability or independently validated physical condition**.

The display must retain the label `EXPERIMENTAL HEALTH INDEX`. Invalid electrical quality, unknown/nonfinite score or ineligible study regime produces no numerical index. Quality findings, raw model ratios, sensor availability, hypotheses and trend evidence remain separately inspectable.

The fixed mapping was selected for a bounded demonstration and was not learned from failures. Saturation at zero or one hundred cannot be interpreted as failure or perfect health. Quiet synthetic signals do not establish industrial health. The dashboard uses research severity categories and does not yet implement every original WATCH/UNKNOWN/stale-state transition requirement.

Tests verify null health for invalid evidence and honest labeling. Calibration against maintenance outcomes, long-term drift, operating-state transitions and intervention recovery is outstanding. This score must not be extrapolated to produce failure dates or service windows.
