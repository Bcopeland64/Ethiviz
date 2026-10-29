# EthiViz V9 — Verifiable Operations and Responsible Analysis

EthiViz analyses text and images through seven ethical traditions: Western, Ubuntu,
Confucian, Islamic, Buddhist, Hindu/Dharmic, and Indigenous/First Nations. Results are
exploratory decision-support signals—not legal determinations, validated fairness
certifications, or substitutes for domain expertise and community review.

V9 is an independent project snapshot in `Ethiviz_V9/`, based on V8. It adds
retry-safe job submission, enforced job-state transitions, queued-job cancellation,
fail-closed Redis configuration, health/readiness endpoints, terminal-job retention,
an end-to-end API benchmark, and accessible progress/cancellation announcements.

## What's new in V9

- **Job lifecycle:** Persistent states cannot be moved backward or overwritten after a
  terminal result. `Idempotency-Key` replays the original job for identical requests and
  returns `409` if the same key is reused with a different payload. Only SHA-256 digests
  of the key, request scope, and uploaded bytes are stored for retry matching.
- **Cancellation semantics:** `POST /api/jobs/{job_id}/cancel` cancels work only while it
  is still queued. Running analysis is not interrupted; the API returns `409` and states
  that the job continues rather than implying it stopped.
- **Operational health:** `/health/live` reports process liveness. `/health/ready` returns
  `503` unless the database, queue, and worker availability checks pass. A configured but
  unreachable Redis queue now fails startup instead of silently switching to local mode.
- **Retention:** uploaded files are swept after 168 hours by default. Completed, failed,
  and cancelled job records/results are purged after 720 hours; set
  `ETHIVIZ_JOB_RETENTION_HOURS=0` to disable job expiry. Explicit job deletion removes
  application-managed result rows/files and retains minimal audit events. This does not
  erase backups, proxy logs, or external Redis persistence.
- **API benchmark:** `Scripts/benchmark_api.py` measures submit-to-result wall time,
  execution time, result retrieval, and queue delay when the server exposes both
  timestamps. It records unavailable resource measures as `null` and never writes input
  content to the report. It does not establish a production capacity limit by itself.
- **Accessible status:** progress and terminal states are announced with live regions;
  queued cancellation and its limitations are surfaced in the interface.
- V8's deferred charts, bundle budget, bounded language cache, API exposure controls,
  deployment headers, and dependency checks remain part of this snapshot.

## Quick start

### Requirements

- Python 3.10 or newer
- Node.js 20 and npm
- A modern browser (Safari 16.4+, Chrome 111+, or Firefox 128+)

From the repository root:

```bash
bash start_ethiviz.sh
```

The frontend is available at `http://localhost:5173`, and the API listens on
`http://127.0.0.1:5001` by default. For API-key protection, set `ETHIVIZ_API_KEYS` in
the environment before starting the server. Do not expose an unauthenticated server to
your network.

For the frontend only:

```bash
cd Ethiviz_V9/project
npm ci
npm run dev
```

For the backend only:

```bash
cd Ethiviz_V9
pip install -e ".[api]"
python Scripts/api_server.py
```

To bind a production-configured instance to a network interface, set `ETHIVIZ_ENV`
to `production`, configure one or more comma-separated `ETHIVIZ_API_KEYS`, and set
`ETHIVIZ_HOST`. Review the reverse-proxy, CORS, TLS, secret-rotation, and data-retention
settings before deployment. The Flask development server is not a production WSGI server.

## Benchmarking

Use a representative, consented input file; the tool does not create or ship a ground-
truth evaluation dataset. Run the server and queue/worker configuration you intend to
measure, then use:

```bash
cd Ethiviz_V9
python Scripts/benchmark_api.py \
  --input sample_data/text/product_reviews.txt \
  --iterations 5 \
  --output benchmark-api.json
```

Set `ETHIVIZ_API_KEY` in the benchmark process when API authentication is enabled. The
report records the revision, runtime/platform, queue/database mode, workload byte count,
sample counts, and p50/p95 timings. Queue delay is `null` if it cannot be derived from
the API timestamps. Peak memory, CPU/GPU utilization, throughput under concurrent load,
image workload coverage, and a production Redis/PostgreSQL reference profile remain
unmeasured here. Compare runs on identical hardware, model, workload, worker settings,
and cache state; timing does not establish analysis quality or score equivalence.

## Safety, data, and limitations

- Uploads are size/type checked and subject to request, quota, queue, image-pixel, and
  source-file retention safeguards. Terminal jobs and their application-managed results
  expire after the configured period. Deletion is not proof that backups, proxy logs, or
  external Redis copies were erased.
- API key authentication and job ownership are server enforced when configured. Browser
  `sessionStorage` reduces persistence across browser sessions but does not defend
  against same-origin script compromise.
- Image interpretations depend on optional computer-vision components and can be
  incomplete or proxy-based. Do not use inferred demographic attributes to make
  consequential decisions about people.
- A qualified, consented, human-reviewed evaluation corpus is not included. No accuracy,
  calibration, fairness, or cross-cultural validity claim should be treated as
  independently established until reviewers, consent, provenance, adjudication, and
  held-out evaluation results are documented.
- Group-fairness and mitigation operations require suitable protected-group labels and
  valid prediction/outcome data; they are not default product workflows.

## Validation

```bash
cd Ethiviz_V9
pytest tests -q
cd project
npm ci
npm test -- --runInBand
npm run build
```

The repository-level workflow at `../.github/workflows/ethiviz-v9-ci.yml` validates V9
backend/frontend changes and enforces the production npm audit and entry-bundle budget.
The backend suite was run locally on 2026-10-29: **259 passed, 7 skipped**. Frontend
tests/build remain unverified in this environment because V9's npm dependencies are not
installed; the build command reported `vite: not found`. Dependency installation was
deferred while required Codacy analysis was unavailable.

## Project structure

```text
Ethiviz_V9/
├── ethiviz/                  # Analysis engine and seven ethical lenses
├── Scripts/                  # Flask API, queue workers, and benchmark utility
├── project/                  # React/Vite interface
├── tests/                    # Backend and regression tests
├── deploy/                   # Container and reverse-proxy configuration
├── docs/                     # Data governance and compliance notes
└── README.md
```

Earlier version folders remain separate historical snapshots. See the repository root
README and [`VERSION_9_IMPROVEMENT_PLAN.md`](../VERSION_9_IMPROVEMENT_PLAN.md) for
implementation status and the deployment- or community-evidence work that remains open.
