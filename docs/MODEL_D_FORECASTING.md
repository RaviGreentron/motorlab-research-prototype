# Model D — physical-feature forecasting

The implemented comparison forecasts an independent simulated temperature trajectory in °C sampled once per minute. It is separate from six-channel waveform anomaly scoring and is not an observed motor degradation history. Methods are last-value naive, ordinary linear trend, Theil–Sen robust trend and additive Holt exponential smoothing.

Expanding-origin evaluation starts after 40 observations, forecasts five steps and advances five steps. The implementation rejects overlapping evaluation horizons (`step < horizon`), so an earlier origin's complete residual is available before it calibrates a later interval. After four earlier origins, the per-horizon 90th-percentile absolute residual gives symmetric empirical bands. Final future bands use all completed backtest residuals. These are descriptive intervals; nonstationary drift can cause substantial undercoverage.

Outputs include MAE, RMSE, bias, sMAPE, error by horizon, empirical coverage, the number of coverage origins, inference time per origin, forecasts and bounds. No real motor RUL is derived from temperature alone. ARIMA, change-point-aware forecasting and nonlinear alternatives are not implemented in the classical comparison module. A separate quadratic simulator-only threshold-crossing module is documented in RUL_AND_DEGRADATION.md.

## Foundation-model feasibility, not execution
The [TimesFM repository](https://github.com/google-research/timesfm) now distinguishes 3.0 with noncommercial/nonproduction weight terms from Apache-licensed 2.5 (200M parameters, 16k context, up to 1k horizon). A model-specific license choice is required; repository-code licensing cannot be assumed to cover every checkpoint.

The [Chronos repository](https://github.com/amazon-science/chronos-forecasting) documents Chronos-2 (120M) and smaller Bolt variants including tiny (9M). These require separate dependencies and checkpoints. Context/horizon and device behavior are variant-specific.

No foundation weights were downloaded. No CPU/GPU memory, latency, zero-shot advantage or fine-tuning benefit was measured. Their industrial value remains **NOT RUN**, with classical results providing the future comparison baseline.
