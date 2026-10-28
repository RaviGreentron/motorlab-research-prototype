# Research findings and suitability decision

**Decision: INCONCLUSIVE for real motors; REVISE normal-load false alarms before any industrial trial.** The prototype is a reproducible research baseline with functioning software paths and bounded synthetic evidence, not a validated maintenance system.

Analytical tests support correct on-bin RMS, frequency and paired phase-to-neutral power calculations. Quality gates reject deliberately corrupted windows. Separate fit, early-stop, calibration and test partitions prevent the tested leakage paths; repeat execution reproduced waveform hashes and detector metrics. These are useful foundations for future measured-data work.

Statistics and the autoencoder detect the injected electrical positives at the reference setting but produce 24.0% and 26.7% negative-window false alarms. Isolation Forest reduces that rate to 18.7% while missing positive windows. Normal load variation is an important confounder. Two operating regimes and narrow healthy calibration sets do not represent the complete normal operating envelope. The autoencoder has not demonstrated a decisive advantage over the simpler baseline.

Window experiments expose a resolution/computation/sensitivity tradeoff. They do not establish an optimum for MCSA because real slip, speed, labels and anti-alias characteristics are unavailable. Optional vibration/thermal evidence can drive the experimental fusion path, but different label targets and uncalibrated scales prevent a claim of proven multisensor improvement.

Holt forecasts the chosen synthetic thermal trajectory better than naive/linear/robust baselines. Poor linear/robust interval coverage demonstrates why forecasting intervals require backtesting. No foundation-model improvement is established. Toy RUL crossing results are conditional on a known quadratic simulator and cannot transfer to motor lifetime.

Public [xPump](https://www.einnosys.com/xpump/) and the vendor's [industrial guide](https://www.einnosys.com/ai-motor-predictive-maintenance-industrial-guide/) motivated monitoring, anomaly investigation and advisory concepts. They provide no verified proprietary algorithm contract for this implementation. Vendor marketing outcomes are not evaluation evidence for MotorLab.

The next scientifically useful step is a frozen, permissioned measured dataset with calibrated synchronized units, motor/load/speed context, independently verified healthy spans and fault/maintenance timestamps. Compare methods on entire held-out motors and future time, use realistic exposure denominators, calibrate alert persistence, and seek engineer-approved false-alarm/recall criteria before promotion.
