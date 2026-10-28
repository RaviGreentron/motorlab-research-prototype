# Data contracts

## Electrical record
`timestamps`: N integer microseconds on a regular sample grid. `values`: N×6 numeric array ordered `ac_current_1`, `ac_current_2`, `ac_current_3`, `ac_volt_1`, `ac_volt_2`, `ac_volt_3`. Units must be A/A/A/V/V/V. Metadata carries motor ID, sample rate, source, `SIMULATED` or `MEASURED` provenance, scaling verification, timestamp unit, sensor range and phase convention. Synthetic records explicitly use phase-to-neutral voltage and paired phase currents at 10 kHz.

`SensorContract` defaults describe the simulator. A measured importer must explicitly establish its own metadata; copying simulator defaults does not verify real hardware. Optional per-channel timestamps can expose skew. A common timestamp column alone cannot prove acquisition hardware synchronization.

Quality rejects shape, channel mapping, units, unknown scaling, invalid provenance, noninteger timing, duplicate/backward timestamps, >1% cadence deviation, nonfinite values, insufficient duration, sensor overrange and repeated rail plateaus. No gap interpolation occurs. Unknown phase mapping/convention disables power without discarding otherwise usable RMS.

## Replay and optional sensors
CSV headers are `timestamp_us` plus the six channel names. Integer timestamps are parsed without conversion through floating-point seconds. Caller-supplied metadata and a file SHA-256 accompany replay. The `motorlab.replay` CLI accepts CSV, metadata JSON and output JSON paths plus `--window` and `--overlap`. It produces quality-gated window features and one-minute aggregates; model status stays unavailable pending a separately verified healthy baseline. This is not a measured-data training workflow.

Vibration requires `m/s2`; temperature requires `degC`. Each optional input has values and separate provenance. Bad optional units or numeric quality invalidate that sensor summary. Actual optional sensor acquisition was not verified.

## Derived artifacts
Feature schema is `motorlab.features/1`. Rows preserve motor, simulated time, source metadata, quality, processing configuration, regime, partition and sample seed. Model output adds raw/normalized scores, descriptive contributors, hypotheses and experimental severity. Study manifest includes source hashes, raw-array digest, dependency versions, partition boundaries and model versions. Notes reference run, motor and window index.

Influx org, bucket, measurement, scaling, tag schema, retention, read authorization and credentials remain unverified. There is no implemented live adapter or production database connection.
