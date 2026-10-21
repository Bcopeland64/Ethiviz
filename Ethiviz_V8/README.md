# EthiViz V8 — Measured, Safer Cross-Cultural AI Analysis

EthiViz analyses text and images through seven ethical traditions: Western, Ubuntu,
Confucian, Islamic, Buddhist, Hindu/Dharmic, and Indigenous/First Nations. Results are
exploratory decision-support signals—not legal determinations, validated fairness
certifications, or substitutes for domain expertise and community review.

V8 is an independent, versioned project snapshot in `Ethiviz_V8/`. It builds on V7 with
deferred visualization loading, an enforced compressed entry-bundle budget, bounded
privacy-conscious language-result caching, fail-closed network binding, and repository-
level dependency automation and CI.

## What's new in V8

- **Deferred charts:** Plotly-heavy analysis views load only when their result sections
  are rendered, instead of increasing the initial application download.
- **Bundle budget:** `npm run build` checks the gzip size of initial JavaScript against a
  400 KiB budget. The CI build uses the same check.
- **Language cache:** Normalized inputs are keyed by SHA-256 digest; cache entries contain
  only language labels, expire after five minutes, and are bounded to 2,048 entries.
  Set `ETHIVIZ_DISABLE_LANGUAGE_CACHE=1` to disable reuse, or configure
  `ETHIVIZ_LANGUAGE_CACHE_SIZE` and `ETHIVIZ_LANGUAGE_CACHE_TTL_SECONDS`.
- **Safer API exposure:** The standalone server refuses non-loopback binding without
  configured API keys and refuses to expose Flask's development debugger. API keys in
  the browser are kept in tab-scoped `sessionStorage` rather than persistent
  `localStorage` (they remain accessible to scripts running in that origin).
- **Deployment headers:** The container nginx path adds CSP, frame, MIME-sniffing,
  referrer, and permissions headers. The API already sets security headers on responses.
- **Supply-chain CI:** Root-level GitHub Actions validates V8 backend/frontend changes,
  enforces the production dependency audit and bundle budget, and stores a full npm
  audit report. Dependabot proposes npm and Python dependency updates weekly.
- **Repeatable benchmark output:** The benchmark reports cold execution, warm p50/p95,
  per-phase engine timings, and peak RSS as JSON. It explicitly marks queue wait as
  unmeasured because this direct-engine benchmark bypasses the API queue.

## Quick start

### Requirements

- Python 3.10 or newer
- Node.js 20 and npm
- A modern browser (Safari 16.4+, Chrome 111+, or Firefox 128+)

From this directory:

```bash
bash start_ethiviz.sh
```

The frontend is available at `http://localhost:5173`, and the API listens on
`http://127.0.0.1:5001` by default. For API-key protection, set `ETHIVIZ_API_KEYS` in
the environment before starting the server. Do not expose an unauthenticated server to
your network.

For the frontend only:

```bash
cd project
npm ci
npm run dev
```

For the backend only:

```bash
pip install -e ".[api]"
python Scripts/api_server.py
```

To bind a production-configured instance to a network interface, set `ETHIVIZ_ENV`
to `production`, configure one or more comma-separated `ETHIVIZ_API_KEYS`, and set
`ETHIVIZ_HOST`. Review the reverse-proxy, CORS, TLS, secret-rotation, and data-retention
settings before deployment. The Flask development server is not a production WSGI server.

## Benchmarking

Use a representative, consented input file; the tool does not create or ship a ground-
truth evaluation dataset.

```bash
python Scripts/benchmark_analysis.py \
  --input sample_data/text/product_reviews.txt \
  --limit 100 \
  --iterations 5 \
  --output benchmark.json
```

The report records Python/platform/CPU information, peak resident memory where the OS
exposes it, cold and warm engine phases, and warm wall-time percentiles. Queue delay is
explicitly `null`; queue wait, throughput under load, image throughput, and GPU
utilization require separate deployment-level measurement. Compare runs on the same
hardware, model, language mix, worker settings, and cache state. Timing results do not
establish score equivalence or analysis quality.

## Safety, data, and limitations

- Uploads are size/type checked and subject to existing request, quota, queue, image-pixel,
  and source-file retention safeguards. Job records, results, logs, backups, and Redis
  retention still require deployment-specific review; deletion of a job is not by itself
  proof that every backup or external log copy was erased.
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
pytest tests -q
cd project
npm ci
npm test -- --runInBand
npm run build
```

The repository-level workflow at `../.github/workflows/ethiviz-v8-ci.yml` runs on pushes
and pull requests affecting V8 and enforces the production npm audit and entry-bundle
budget.

## Project structure

```text
Ethiviz_V8/
├── ethiviz/                  # Analysis engine and seven ethical lenses
├── Scripts/                  # Flask API, queue workers, and benchmark utility
├── project/                  # React/Vite interface
├── tests/                    # Backend and regression tests
├── deploy/                   # Container and reverse-proxy configuration
├── docs/                     # Data governance and compliance notes
└── README.md
```

Earlier version folders remain separate historical snapshots. See the repository root
README for the version index and the V8 improvement plan for work that remains gated on
community governance or deployment-specific evidence.
