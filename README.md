# MotorLab research prototype

Local industrial motor condition-monitoring research: FastAPI, React/TypeScript, signal processing, robust statistics, Isolation Forest, a CPU autoencoder, and classical forecasting.

**Synthetic research only. Not validated for industrial maintenance decisions.** Real motor RUL is disabled; live InfluxDB is not connected. See [known limitations](docs/KNOWN_LIMITATIONS.md) and [research assessment](RESEARCH_REPORT.md).

## Run on Windows

Install Python 3.12. In PowerShell:

```powershell
cd prototype
./setup.ps1 -PythonPath python
./.venv/Scripts/python.exe -m motorlab.experiment --seed 42 --window 1
./start.ps1
```

Open http://127.0.0.1:8765/. The built dashboard is included; Node is needed only when changing frontend source. Stop the server with Ctrl+C.

## Run on Linux/macOS

```sh
cd prototype
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m motorlab.experiment --seed 42 --window 1
python -m uvicorn motorlab.api:app --host 127.0.0.1 --port 8765
```

The dependency lock was verified on Windows/Python 3.12; other operating systems have not been verified.

## Verify and develop

After generating the initial study, run `python -m pytest tests -q` from `prototype` in the environment. `python validate_research.py` reruns the multi-window research matrix. For the dashboard, use Node and pnpm: `cd frontend`, `pnpm install --frozen-lockfile`, then `pnpm build`.

The delivered Windows build had 67 pytest passes, 15 browser workflow checks and five focused UI checks. Those are recorded historical results, not a claim that GitHub CI has run.

## Repository layout

- `prototype/motorlab`: ingestion, DSP, model, forecast, intelligence and API modules
- `prototype/frontend`: React source and built dashboard
- `prototype/tests`: analytical, model, replay and API tests
- `docs`: 22 technical documents and OpenAPI contract
- `data`: generated locally, excluded from version control

Local environments, credentials, model pickle files, SQLite notes and generated research runs are excluded. Reproduce runs locally; source documents may refer to evidence files from the original delivery that are intentionally not included here.

This project does not copy proprietary xPump algorithms or claim equivalent performance. No open-source license has yet been selected by the owner.
