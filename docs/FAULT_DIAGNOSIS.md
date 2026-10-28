# Fault-hypothesis specification

Diagnosis remains separate from anomaly detection. Rules currently identify feature-level voltage imbalance (>3%), current imbalance (>5%) and abnormal current harmonics (>8% THD). These thresholds are illustrative research settings. Phase-current RMS ratio below 0.1 may yield **Phase loss or sensor fault**, only when all three currents are known and finite.

Each hypothesis includes supporting measurements, required verification, a method label, evidence strength, validation status and limitations. The contradictory-evidence list is currently empty; a comprehensive differential-diagnosis engine is not implemented. Hypotheses are `SYNTHETIC_ONLY`, not confirmed faults.

An elevated score without a supported rule returns `ANOMALY_DETECTED_CAUSE_UNKNOWN`. Invalid quality or missing/nonfinite score returns UNASSESSABLE and no health estimate. Missing phase measurements are not converted to observed zero current.

No confirmed bearing, stator, rotor, eccentricity or overload classifier exists. Exploratory MCSA frequencies do not automatically create a rotor diagnosis. Electrical evidence alone does not establish temperature or bearing failure. Simulated optional channels retain their own provenance.

Research recommendations are Observation, Inspection suggested, or Urgent engineering review according to experimental score. They do not issue work orders, stop motors or schedule repairs. A real deployment would require motor ratings, physical wiring, sensor validity, operating context, competing-cause evidence and labeled validation.
