# Known limitations and unmet scope

## Scientific limits
- All evaluated motor evidence is synthetic. Generator fault labels, short five-window scenario blocks and related simulated motors do not establish field sensitivity or reliability.
- Substantial normal-condition false alarms remain. Experimental 99th-percentile thresholds were not approved as industrial acceptance limits.
- Harmonic and fundamental estimates are nearest-bin methods; off-bin variation/leakage and short windows need stronger validation. Hardware synchronization, anti-aliasing, sensor drift and physical calibration are not established.
- CUSUM/EWMA diagnostics operate over filtered per-regime selections in the study and are not a production gap-aware streaming state machine.
- False-event metrics count false-positive window runs within scenario blocks. Window intervals ignore temporal dependence; motor-day extrapolation from seconds is unstable. Delay is scenario-window delay, not physical failure lead time.
- The forecast is an independent simulated temperature trajectory, separate from the selected motor's electrical windows. Empirical intervals can under-cover; linear/robust models perform poorly on accelerating drift.
- Toy threshold-crossing RUL assumes the generator's quadratic mechanism and arbitrary 70°C endpoint. Real RUL and service dates remain unavailable.
- Fusion scales and health mapping are illustrative, not calibrated. Optional-sensor metrics do not prove controlled improvement over electrical-only models.

## Unimplemented or partial capabilities
- No live Influx adapter, authorization verification workflow, database read-throughput benchmark or prospective industrial shadow test.
- Offline CSV CLI generates validated features/aggregates but has no verified measured baseline, model training or dashboard import flow.
- No PyTorch/GPU autoencoder, sequence network, supervised fault classifier, comprehensive differential diagnosis, learned fusion or full uncertainty calibration.
- No TimesFM/Chronos download or runtime evaluation; ARIMA/change-point-aware forecasting is not implemented.
- No dedicated Parquet/time-series feature store, full waveform archive, streaming scheduler, advanced retention or complete model registry API.
- UI consolidates screens and endpoints; all original stale/unknown/watch states, comprehensive filtering, feature selection, forecast configuration and adjudication workflows are not complete.
- Local-only origin protection is not production authentication. No internet-facing deployment or multi-user operational security claim.

## Evidence limits
67 passing pytest tests and recorded browser checks cover specified fixtures/workflows, not every requirement. Seven studies plus one deterministic repeat are a small research matrix, not statistical proof across loads, motors or failure populations. Runtime measurements are local process snapshots and exclude several production costs. The deliverable is a completed **bounded prototype**, with the above unmet requirements explicitly carried forward.
