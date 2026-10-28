# Local API specification

FastAPI exposes `/docs` and `/openapi.json` as the executable contract. The intended listener is loopback port 8765. Production credentials and Influx clients are not imported. The frontend build is served at `/` when present.

| Method and path | Contract |
|---|---|
| GET `/api/v1/health` | Local service status, SIMULATED provenance, production_access=false |
| GET `/api/v1/runs` | Pagination: limit 1–100, offset ≥0; run identifiers |
| GET `/api/v1/runs/latest` | Full latest immutable report, or 404 |
| POST `/api/v1/runs` | Seed 0..2³¹−1; window_seconds one of .1/.2/.5/1/2/5; overlap exactly 0; unknown fields rejected; 201 on completion |
| GET `/api/v1/runs/{run_id}/export` | Full report JSON with attachment header |
| GET `/api/v1/runs/{run_id}/waveform` | Required motor_id; index 0..239; deterministic selected excerpt and spectrum with provenance/quality |
| GET `/api/v1/runs/{run_id}/features` | motor_id, relative start/end seconds, limit 1–500 and offset; half-open time selection |
| GET `/api/v1/runs/{run_id}/notes` | Saved local research annotations |
| POST `/api/v1/runs/{run_id}/notes` | SIM-01/02/03, index 0..239, text 1..4000 characters; 201 |
| GET `/api/v1/capabilities` | Influx blocked and RUL unavailable |

The run operation is synchronous and process-local locking rejects concurrent runs with 409. Expected errors use an `error` object with code/message; input validation returns 422. Run IDs are constrained before filesystem lookup. SQL parameters protect note contents. Browser mutation origins are restricted to the configured loopback ports.

This is not authenticated multi-user hosting. Binding publicly is unsupported. Separate inventory/model registry/forecast endpoints from the original design are consolidated into report fields, not individually implemented. There is no CSV upload endpoint or live Influx query endpoint. Waveform response is a bounded excerpt, not full historical range retrieval. Generic unexpected errors are not a complete production error taxonomy.
