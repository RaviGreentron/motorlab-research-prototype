# Degradation and RUL status

Real motor RUL is **RUL_NOT_ESTIMABLE** throughout this prototype. There are no verified measured degradation trajectories, defined validated failure endpoints or independent failure-event backtests. Service windows remain null.

The library's `rul_eligibility` helper returns ELIGIBLE_FOR_RESEARCH only when a caller supplies an endpoint, at least three histories and a validated flag. It is a prerequisite check, not an estimator or verification of those supplied claims. Three histories is an illustrative software gate, not a scientifically sufficient sample-size rule.

Synthetic electrical degradation raises current amplitude inside independently generated windows. A separate quadratic-plus-noise simulated temperature series supports classical forecast evaluation. Neither is a physical lifetime model.

The separate `synthetic_rul.py` experiment fits a quadratic trajectory and residual-bootstrap samples 200 fits. It estimates steps until the arbitrary simulator endpoint 70°C, returning SYNTHETIC_RUL_ONLY if at least 90% of draws cross within the search horizon; otherwise it returns RUL_NOT_ESTIMABLE. At origins 60/80/100/120, actual remaining steps are 90/70/50/30 and predicted medians are 92/71/51/30. Recorded MAE is 1 step (one minute) and empirical interval coverage is 4/4. Evidence resides in `validation-summary.json`.

These conditional intervals assume the known quadratic generator, resampled residual behavior and an arbitrary fixed threshold. Four successful origins do not validate 90% population coverage or any real failure temperature. The result is kept separate from the dashboard's real-motor RUL status and cannot justify a maintenance date.

Supported outlook is therefore feature trend, empirical forecast interval and explicit evidence limitations. Future RUL work requires a failure or validated service threshold, representative trajectories with operating context, censored-history handling, endpoint uncertainty, rolling backtests and error/coverage reporting. Forecasting a temperature or current change alone cannot establish remaining useful life.
