# Measured performance

Source: `outputs/data/validation-summary.json`, seven completed studies. Environment reported Windows 11 build 26200, Python 3.12.14, 24 logical CPUs and 30.88 GiB RAM. GPU was not used. Exact processor model was not available from the permitted inventory. Recorded library versions include NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, FastAPI 0.162.0 and statsmodels 0.15.0.

| Window s / seed | DSP median ms | DSP p95 ms | Study elapsed s | Resident memory MiB |
|---|---:|---:|---:|---:|
| 0.1 / 42 | 3.197 | 3.839 | 3.37 | 181.6 |
| 0.2 / 42 | 3.792 | 5.396 | 4.15 | 195.8 |
| 0.5 / 42 | 5.268 | 6.942 | 5.54 | 202.7 |
| 1 / 42 | 8.086 | 10.901 | 8.18 | 207.2 |
| 2 / 42 | 15.064 | 22.072 | 14.69 | 213.1 |
| 5 / 42 | 38.940 | 58.890 | 37.65 | 224.3 |
| 1 / 7 | 7.593 | 10.717 | 7.87 | 236.6 |

DSP timing covers extraction for each generated window, including quality work and outputs. Invalid windows return early, so the aggregate is not a pure valid-window FFT throughput measurement. Study elapsed time includes simulation, fitting, scoring and forecasting up to report construction; final file serialization is outside that recorded endpoint. RSS is a point-in-time process measurement, not peak or incremental per-model memory. Later runs share a process and can retain allocations.

The reference forecast mean times per rolling origin are naive 0.028 ms, linear 0.063 ms, robust 0.906 ms and Holt 7.302 ms. Detector-suite training and inference timings are recorded per motor/regime in each run, not separately attributed to each constituent detector.

These measurements indicate the bounded local workload runs on this CPU. They do not prove sustained 60,000-scalar/s ingestion, database throughput, production streaming latency, simultaneous-user capacity or end-to-end industrial latency. Acquisition window duration, I/O, queues and dashboard rendering add costs absent from DSP timing. No live database, network, GPU, foundation-model or large-history benchmark was run.

Additional loopback API measurements, five samples per route, are saved in `outputs/data/api-benchmark.json`: `/` median 2.547 ms (max 70.646 ms), `/api/v1/health` median 0.899 ms (max 1.717 ms), and `/api/v1/runs/latest` median 296.404 ms (max 375.757 ms). They measure local response behavior for the generated study rather than external database/network latency. The launcher was verified separately. Browser workflow checks establish function, not a comprehensive rendering-performance benchmark.
