# Dashboard implementation and display contract

The local React/TypeScript application provides eight navigation views: Overview, Waveform analysis, Anomaly investigation, Predictive outlook, Model comparison, Maintenance review, Study configuration and Data quality. Charts are SVG components rather than ECharts/Plotly; this keeps the bounded interface small while retaining visible axes, legends and accessible image labels.

Persistent context includes selected simulated asset, immutable run ID, window duration and creation time. SIMULATED provenance and a synthetic-validation warning remain visible. Run creation has loading/success/error feedback. Empty or invalid chart data shows an explicit no-valid-observations state. Real RUL is Not estimable.

Waveforms show up to 1,200 raw samples per selection; spectra show a bounded phase-1 subset, not an unlimited high-rate rendering. Available feature values are displayed with physical units. Forecast labels must match the report's temperature °C and cadence; no electrical interpretation may be inferred from the thermal series.

Model evidence presents normalized ratio and raw score. Baseline contributors are labeled descriptive, not causal attributions. A null score must not be interpreted as normal. Quality and eligibility differ: valid transition waveforms may still be unscored.

The implementation includes responsive navigation, keyboard-accessible primary controls, notes and download. It is not a comprehensive accessibility certification. Full stale-stream behavior, live outage states, arbitrary sensor configuration, rich event adjudication and every original screen-state variant are not implemented. Browser verification evidence and screenshots are reported separately in the validation summary; existence of UI source alone does not count as E2E PASS.
