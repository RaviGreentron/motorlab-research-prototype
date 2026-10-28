# Implemented user flows

## Create and inspect a study
Open the local dashboard, select Study configuration, choose seed and analysis duration, then Run experiment. A new run ID preserves its configuration/results. The source is synthetic; replay and Influx choices are disabled. The UI returns to Overview when the synchronous experiment completes. Export study downloads its report JSON.

## Investigate an observation
Select SIM-01/02/03, open Waveform analysis or Anomaly investigation, and choose a window index. The API regenerates its recorded scenario and seed. Inspect current/voltage traces, phase-1 spectrum, data quality, A/B/C scores and robust deviations. Invalid windows have no derived spectrum or model result. Ground-truth scenario labels are simulation context, not model diagnoses.

## Annotate and review maintenance evidence
Enter a research note in Anomaly investigation and save it to the run/motor/window. Notes persist in local SQLite and reappear after refresh. Maintenance review shows hypotheses, experimental health, recommended engineer review and unavailable real RUL. It performs no external action.

## Compare forecasting and detectors
Model comparison displays held-out electrical detector metrics, separate fusion metrics, classical forecast errors, runtime and manifest. Predictive outlook allows forecast-method selection for the separately simulated temperature series. Forecast and anomaly objectives are not ranked against each other as one score.

## Quality investigation
Data quality lists all windows and rejection reasons. Selecting a row opens the corresponding waveform. Rejected data is not silently filled. Startup/shutdown can be numerically valid but unassessable for the steady-regime model; data validity and model eligibility are different.

Offline users can run `python -m motorlab.replay input.csv metadata.json result.json --window 1 --overlap 0.5` from the prototype environment. This produces feature/quality output, not a scored dashboard study. Historical replay study creation, dashboard dataset import, live read authorization, arbitrary feature/model configuration and event-level adjudication states remain future workflows.
