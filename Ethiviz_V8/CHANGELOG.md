# Changelog

## 0.11.0 — EthiViz V8

- Deferred chart-heavy frontend views and added a gzip initial-entry bundle budget.
- Added a bounded TTL language-result cache keyed by normalized-text digests, with an
  operator disable switch.
- Refused non-loopback API binding without configured API-key authentication and blocked
  debug-mode network exposure.
- Switched browser API-key persistence from `localStorage` to tab-scoped `sessionStorage`.
- Added reproducible cold/warm benchmark summaries and root-level dependency CI.
- Human-reviewed evaluation data, calibrated accuracy claims, queue-level benchmarks,
  distributed cancellation, and end-to-end backup retention remain explicitly gated;
  see `README.md` and `VERSION_8_IMPROVEMENT_PLAN.md`.

## 0.10.0

Tier 6 (Upgrades 51, 52, 54) — EthiViz V7 Phase 3, "Activate the Dormant
Engine." Previous tiers built and secured the platform; this one makes
data the engine has computed since V6 actually reach a caller, instead of
being silently dropped in `Scripts/ethiviz_bridge.py` before the response
ever left the server. Upgrade 53 (mitigation preview) is explicitly
deferred, not built — see "Cut from this tier" below.

Test suite: 223 → 239 tests (`tests/test_v7_phase3.py`).

### Added — Tier 6 upgrades

- **Upgrade 51 — Dimension-level findings, conflicts, and synergies.**
  `Analyzer.analyze()` has computed `construct_readings` (which shared
  moral construct a dataset triggers, and whether the 7 traditions
  converge on it or only one flags it — `ethiviz/frameworks/
  dimension_map.py`), `conflicts`, and `synergy_amplifications` since V6,
  but `ethiviz_bridge.py` discarded all three before they reached
  `api_server.py`'s response. A completed text job's `results` now
  includes a `dimension_findings` key (`construct_readings`,
  `consensus_findings`, `tradition_specific_findings`, `conflicts`,
  `synergy_amplifications`); the frontend gained a
  `DimensionFindingsPanel.tsx` rendering the consensus vs.
  tradition-specific split. Also fixed while wiring this: `MainContent.tsx`
  rendered `CrossCulturalEquityDashboard`'s Synergies/Conflicts cards
  without ever passing the `synergies`/`conflicts` props — both always
  showed their "none detected" empty state regardless of what the engine
  actually found, for every job, since those components were first added.
  Per-lens `analysis_coverage` (already computed, same drop-before-response
  pattern) is now surfaced on each `tradition_scores` entry too, following
  the same "only show it as a caveat" rule already used for
  `translation_reviewed`/`warnings`.
- **Upgrade 52 — Individual fairness metric (opt-in).**
  `ethiviz/metrics/individual_fairness.py`'s consistency/sample-distortion
  check — "do similar inputs get similar scores?" — is wired into
  `compute_tradition_scores` behind `advanced_options
  .include_statistical_metrics` (new checkbox in ConfigPanel.tsx's Advanced
  Options panel, previously a display-only placeholder with a literal
  `TODO: Add inputs to change these options`), run per-lens directly on the
  per-text scores the engine already produces. Group fairness (SPD/DI/EOD/
  AOD, `ethiviz/metrics/group_fairness.py`) is deliberately NOT wired here —
  see "Cut from this tier." New `StatisticalFairnessPanel.tsx` renders the
  per-tradition table when present.
- **Upgrade 54 — `severity_thresholds` parsing; demographic stubs removed.**
  `CulturalFramework` (`ethiviz/frameworks/base.py`) gained a
  `severity_thresholds` field, now parsed by `FrameworkLoader.load_file`
  from the block every builtin YAML already declared but that was silently
  discarded. `ethiviz_bridge._severity_for` now reads each framework's own
  thresholds from the live `Analyzer` registry instead of importing
  `TRADITION_THRESHOLDS` from `ethiviz/metrics/group_fairness.py` — an
  unrelated AIF360 group-fairness-difference-metric table that happened to
  share the same numbers (verified byte-identical) but was never the
  YAML's own declared source. The same relative rescaling `_severity_for`
  already did is kept, since the raw cutoffs are still on that ~0-0.3
  scale, not this engine's own 0-1 score — using them literally would
  collapse every flagged score straight to "critical." `compute_age_
  distribution`/`compute_gender_distribution` (`ethiviz/analysis/
  demographics.py`) were real stubs — always returned `{}`, referenced
  nowhere else in the codebase — deleted per the "no half-finished
  implementations" standard, rather than left silently returning nothing
  forever.

### Cut from this tier (documented, not silently dropped)

- **Group fairness (SPD/DI/EOD/AOD) and every `ethiviz/mitigation/`
  algorithm (Upgrade 53)** require protected-attribute group labels —
  which row belongs to a protected group — that nothing in this app
  collects; it produces bias *scores* on content, not group-labeled
  predictions. Backing a Group Fairness or Mitigation Preview panel with
  data that doesn't scientifically support it would repeat the exact
  failure mode V6 was built to fix (metrics structurally incapable of
  measuring what they claimed). Wiring these for real means adding a way
  to collect protected-attribute labels first (e.g. a column-tagging UI
  for uploaded datasets) — genuinely new product surface, not just wiring,
  and deliberately out of scope here. See README.md's "Known limitations."

## 0.9.0

Tier 6 (Upgrades 46-50) — EthiViz V7 Phase 2, "Scalable Production
Architecture." 0.8.0 closed the auth/rate-limit/TLS gap but left the app a
single process with no queue, no way to share state across instances, and
no visibility into what it was doing once deployed. This tier replaces the
unbounded per-request thread with a real, bounded queue; fixes the
concurrent-calibration race the 0.8.0 README still flagged as open; adds an
opt-in Postgres backend so the API and worker processes can share a
database; ships a Dockerfile/docker-compose stack; and adds structured
logs and a Prometheus `/metrics` endpoint.

Test suite: 201 → 223 tests (`tests/test_concurrency.py`,
`tests/test_v7_phase2.py`; 7 of the latter are Postgres-only and skip
without `ETHIVIZ_TEST_DATABASE_URL`).

### Added — Tier 6 upgrades

- **Upgrade 46 — Real task queue.** `Scripts/analysis_queue.py`'s
  `AnalysisQueue` replaces `/api/analyze`'s unbounded
  `threading.Thread(target=run_analysis_job, ...)` per request. Without
  `ETHIVIZ_REDIS_URL`, it runs jobs on a bounded local `ThreadPoolExecutor`
  (`ETHIVIZ_LOCAL_WORKERS`, default 2) behind a `BoundedSemaphore`
  (`ETHIVIZ_QUEUE_MAX_DEPTH`, default 100) — a full queue now returns 503
  instead of spawning another thread regardless of load. Setting
  `ETHIVIZ_REDIS_URL` switches to RQ, with one automatic retry
  (`Retry(max=1, interval=[5])`) on a crashed job and a documented
  `ETHIVIZ_JOB_TIMEOUT` (default 3600s); `python Scripts/worker.py` is the
  new worker entry point, run as one or more separate processes. An
  unhandled exception in a locally-queued job is now logged (it would
  previously vanish silently — `ThreadPoolExecutor` doesn't surface an
  exception unless something calls `future.result()`, which nothing did).
- **Upgrade 47 — Thread-safe calibrator/drift state.** `PlattCalibrator`
  (`ethiviz/scoring/calibration.py`) gained the same `threading.RLock` +
  atomic-write (`os.replace`) pattern `DriftMonitor` already had from V6
  Upgrade 35, closing the race the 0.8.0 README documented as open and
  unresolved. `tests/test_concurrency.py` runs concurrent `fit()` writers
  against `calibrate()` readers on a shared calibrator instance and asserts
  no corrupted on-disk JSON and no torn tempfiles — nothing in the existing
  suite exercised this across threads before. With Upgrade 46, each RQ
  worker process also gets its own independent `Analyzer` singleton, so
  this is no longer a race across processes either.
- **Upgrade 48 — Postgres backend (opt-in).** `ethiviz/storage/job_store.py`
  is now a thin `JobStore` dispatcher over `_SQLiteBackend` (the original
  implementation, byte-for-byte unchanged, still the default) and a new
  `_PostgresBackend` (SQLAlchemy Core, not the ORM — keeps the same
  explicit-SQL style as the SQLite path), selected via `DATABASE_URL`.
  Verified against a real `postgres:16-alpine` container, including the
  audit hash chain: `_write_audit` uses `pg_advisory_xact_lock` rather than
  the SQLite path's `threading.Lock`, since the API and worker processes
  above are separate OS processes sharing one database — a
  process-local lock alone would let two of them read the same "last"
  row_hash and fork the chain. Stress-tested with 8 threads × 25 writes
  against a live instance (chain stayed valid). Schema creation
  (`CREATE TABLE IF NOT EXISTS`) needed the same treatment — caught by
  actually running `docker compose up` with gunicorn's default 2 workers,
  not by any unit test: two workers constructing `JobStore` at the same
  moment both passed Postgres's existence check before either committed,
  and the second's catalog insert failed with `duplicate key value
  violates unique constraint "pg_type_typname_nsp_index"`. `__init__` now
  takes the same advisory lock before running the schema statements;
  `tests/test_v7_phase2.py::test_concurrent_schema_init_does_not_race`
  reproduces it directly (10 concurrent `JobStore()` calls against an empty
  schema) and confirms the fix. No behavior change for anyone who doesn't
  set `DATABASE_URL`.
- **Upgrade 49 — Containerization + CI.** New multi-stage `Dockerfile`
  (frontend build → Python deps → `runtime` used by both the API and
  worker services → `frontend` nginx image) and `docker-compose.yml` wiring
  API + worker + Redis + Postgres + the built frontend behind nginx
  (`deploy/nginx.docker.conf`), non-root `ethiviz` user throughout. Fixed
  while building it: a plain `pip install` of this package installs 0 of
  the 21 `.yaml` files under `ethiviz/` (setuptools only packages `*.py`
  without explicit package-data config) — the runtime image copies
  `ethiviz/` as source instead of relying on the pip-installed copy, which
  would have silently shipped without any framework/prototype data.
  Root-level `.github/workflows/ci.yml` runs the backend (with a Postgres
  service container for the Upgrade 48 tests) and frontend test suites,
  builds both images, scans the runtime image with `trivy`, and pushes to
  GHCR on merge to `main` (never on a PR build). `ConfigPanel.tsx` and
  `CrossCulturalEquityDashboard.tsx`'s hardcoded
  `API_BASE_URL = 'http://localhost:5001'` — which would have resolved to
  the *browser's* machine, not the server, for anyone but a local
  single-host deployment — is now `import.meta.env.VITE_API_BASE_URL`,
  read at build time; the Compose frontend image builds with it set to
  `''` (same-origin, routed through nginx) while `npm run dev` keeps the
  original default.
- **Upgrade 50 — Observability.** New `Scripts/observability.py`: every log
  line is now structured JSON (timestamp, level, logger, message,
  `request_id`) via a logging filter + formatter installed on the root
  logger before anything else logs a line; a correlation ID is generated
  per request (or echoed back from an incoming `X-Request-ID` header).
  `GET /metrics` (Prometheus text format) reports HTTP request
  counts/latency, analysis job counts/duration by `analysis_type` and
  outcome, `ethiviz_queue_depth` (via Upgrade 46's queue), and
  `ethiviz_lens_warning_rate` — how often each lens attaches a `warnings`
  entry (see `ethiviz_bridge.compute_tradition_scores`) across all scored
  jobs. Subject to `ETHIVIZ_API_KEYS` like every other route when auth is
  enabled, rather than exempted — documented in the README as needing a
  bearer-token-capable scraper.

### Fixed while implementing Tier 6

- `tests/test_smoke.py::test_smoke_8_reproducibility` asserted
  `rec.library_version == "0.6.0"` — stale since 0.7.0, silently passing
  only because nothing had touched it; it went unnoticed until this tier's
  baseline test run. Now asserts against `ethiviz.__version__` so it can't
  go stale again on the next version bump.
- `deploy/gunicorn_conf.py` and `deploy/README.md` still described the
  Upgrade 47 race as unresolved ("keep worker processes low for now") —
  updated now that it's fixed, with a note on how worker count interacts
  with Upgrade 46's optional queue instead.

## 0.8.0

Tier 6 (Upgrades 40-45) — EthiViz V7 Phase 1, "Security Foundation." Closes the
gap 0.7.0's changelog left open: "No authentication exists on any endpoint
and no rate limiting is applied." This tier also fixes a related gap that
tier's own hardening pass didn't reach — the app's documented run command
(`python Scripts/api_server.py`) is Werkzeug's development server, unfit for
non-local traffic — and adds upload content verification, CI dependency/SAST
scanning, and a tamper-evident audit log.

Test suite: 177 → 201 tests.

### Added — Tier 6 upgrades

- **Upgrade 40 — API-key authentication & job ownership.** `ETHIVIZ_API_KEYS`
  (comma-separated, unset by default) gates every route except `/`,
  `/api/sample-data`, and the already-loopback-gated `/api/stop` behind
  `Authorization: Bearer <key>`. Jobs created while a key is presented are
  scoped to that key's hash (`jobs.owner_key_hash`, added via this
  codebase's first schema migration — see `_ensure_column` in
  `ethiviz/storage/job_store.py`); `/api/jobs`, job status/results/export,
  the audit log, delete, and compare all now check ownership, returning 404
  (not 403) on a mismatch so a caller can't distinguish "not found" from
  "belongs to someone else." Jobs created before a key was set, or while
  auth is disabled, remain visible to any authenticated caller — documented,
  not silently swept under.
- **Upgrade 41 — Rate limiting & concurrency caps.** `flask-limiter`
  (`ETHIVIZ_RATE_LIMIT_DEFAULT`, default 120/min API-wide;
  `ETHIVIZ_RATE_LIMIT_ANALYZE`, default 10/min on `/api/analyze` and
  `/api/compare`), keyed by API key when authenticated, else caller IP.
  Separately, `ETHIVIZ_MAX_CONCURRENT_JOBS_PER_KEY` (default 3) caps
  concurrent analysis work in flight per caller — acquired only once a
  request passes validation and is about to start real work, so
  validation-only failures never consume a slot.
- **Upgrade 42 — Production WSGI + TLS deployment path.** New `deploy/`
  (gunicorn config, an nginx TLS-terminating reverse-proxy sample, setup
  instructions) as the production alternative to `start_ethiviz.sh`'s dev
  server; that script is unchanged. Response headers gained
  `Strict-Transport-Security` and `Permissions-Policy`. Added
  `ETHIVIZ_TRUST_PROXY` (`ProxyFix`, opt-in only) — without it, every
  request behind the sample nginx config would read as `127.0.0.1`,
  silently defeating `/api/stop`'s loopback check for anyone going through
  the public proxy; applying it unconditionally would instead let a direct,
  unproxied caller spoof `X-Forwarded-For` to the same effect.
- **Upgrade 43 — Upload content verification & quota.** Extension checking
  (`allowed_file`) only ever inspected the filename. Uploaded files are now
  also checked against their actual bytes after saving: magic-byte
  detection (via `filetype`) for images, a ZIP/OLE2 signature check for
  xlsx/xls, and a NUL-byte sanity check for plain-text formats.
  `ETHIVIZ_UPLOAD_QUOTA_MB_PER_DAY` (default 500) caps total daily upload
  volume per key/IP, independent of the existing 50MB per-request cap. A
  global `PIL.Image.MAX_IMAGE_PIXELS` guard is set at import time (behind
  the same optional-Pillow guard as the rest of the vision pipeline) as a
  decompression-bomb defense.
- **Upgrade 44 — CI dependency & SAST scanning.** No CI existed at all
  before this. New `.github/workflows/security.yml` (at the repository
  root — this project's actual git root is one level above `Ethiviz_V6/`,
  not `Ethiviz_V6/` itself) runs `pip-audit`, `bandit`, and `npm audit` on
  every PR/push to `main`. Flask/flask-cors/flask-limiter/filetype were
  previously installed ad hoc by `start_ethiviz.sh`, invisible to any
  scanner since nothing declared them; added as a new
  `[project.optional-dependencies].api` group in `pyproject.toml`.
  `pip-audit` against the initial floors (`flask>=3.0`, `flask-cors>=4.0`)
  found real, current CVEs in the versions pip resolved to — floors raised
  to `flask>=3.1.3`, `flask-cors>=6.0.0`, `werkzeug>=3.1.6`, verified clean.
  `.github/bandit-baseline.json` (dated 2026-08-19) tracks the small number
  of pre-existing findings outside this tier's scope (vision-pipeline model
  downloads, one `try/except/pass`, the already-documented dev-mode
  `0.0.0.0` bind) so the job fails only on genuinely new findings, not
  silently on everything that already existed.
- **Upgrade 45 — Tamper-evident audit log.** The five places that wrote
  `audit_log` rows (`create_job`, `update_status`, `store_results`,
  `delete_job`, each with its own ad hoc `INSERT`, plus `log_event`) are
  consolidated into one `_write_audit` path so a hash chain covers all of
  them, not just whichever one it was bolted onto. Each row's `row_hash`
  covers the previous row's hash plus its own fields; a
  `threading.Lock` (mirroring `DriftMonitor`'s existing pattern from
  Upgrade 35) serializes the read-last-hash-then-insert sequence so
  concurrent writers can't fork the chain. `GET
  /api/jobs/<job_id>/audit-log?verify=true` recomputes the chain and
  reports the first broken row, if any. Rows written before this migration
  have no hash and are treated as a starting checkpoint, not a failure.

### Fixed while implementing Tier 6

- `Scripts/api_server.py`'s CVE floors above were discovered, not assumed —
  `pyproject.toml`'s initial `api` extras group would have let `pip install`
  resolve to `flask` 3.0.3, `flask-cors` 5.0.1, and `werkzeug` 3.0.3, each
  carrying known, currently-tracked vulnerabilities.

## 0.7.0

Tier 5 (Upgrades 35-39): closes out documented known-limitations and the V5
plan's unanswered self-audit question, plus a production security pass on
the Flask API and one multilingual regression found while writing tests for
this tier.

Test suite: 162 → 177 tests.

### Added — Tier 5 upgrades

- **Upgrade 35 — Thread-safe drift monitoring.** `DriftMonitor.check_drift`
  did an unguarded read-then-write of its baseline/snapshot JSON files;
  concurrent analysis jobs (each running in its own thread in
  `Scripts/api_server.py`) could race and corrupt the on-disk baseline.
  `DriftMonitor` now serializes its read-modify-write cycle with a lock and
  writes snapshots atomically (temp file + rename) as defense in depth.
- **Upgrade 36 — Framework self-audit.** New `ethiviz/frameworks/coverage_audit.py`
  and `GET /api/framework-coverage` report each tradition's prototype count,
  category count, and translation-review status, plus a Framework Coverage
  Index using the same coefficient-of-variation formula as the frontend's
  CREI. This answers the V5 plan's open question of whether CREI should also
  evaluate the tool itself — it currently does not, and the four
  longest-established traditions (western, ubuntu, confucian, islamic) also
  ship translations with no `translation_provenance` block at all, unlike
  the three newer ones. Surfaced in `CrossCulturalEquityDashboard.tsx`.
- **Upgrade 37 — Translation review surfacing.** `Analyzer.analyze()` now
  attaches `translation_reviewed` (`True`/`False`/`None`) and a warning to
  each framework's result when a non-English score depends on a
  machine-generated or provenance-undeclared translation. Previously this
  information existed only as a comment in the prototype YAML files and
  never reached a caller relying on the score.
- **Upgrade 38 — Upload & job retention.** Uploaded source files in
  `api_uploads/` persisted indefinitely with no cleanup path. Added an
  hourly retention sweep (`ETHIVIZ_UPLOAD_RETENTION_HOURS`, default 7 days)
  and `DELETE /api/jobs/<job_id>` for explicit, immediate purge of a job's
  files, SQLite rows, and results.
- **Upgrade 39 — Audit log exposure.** `JobStore` has written a full
  `audit_log` (created/status/results events) since Upgrade 31, but nothing
  ever read it back. Added `GET /api/jobs/<job_id>/audit-log` and a
  `JobStore.log_event()` for events outside the store's own lifecycle
  (export requests now log an `exported` event; deletions log a `deleted`
  event rather than being silently removed from the trail).

### Fixed — multilingual regression found while testing Upgrade 37

- `LanguageDetector.detect()` never matched `langdetect`'s `zh-cn`/`zh-tw`
  return values against `SUPPORTED_LANGUAGES["zh"]`, so every Chinese input
  silently fell back to English scoring — a complete, silent loss of one of
  the six supported languages, hiding inside the very honest-degradation
  system meant to prevent exactly this. Fixed by normalizing to the primary
  language subtag before the lookup.

### Security — production hardening

- Flask ran with `debug=True` on `host='0.0.0.0'` unconditionally. The
  Werkzeug debugger exposes an interactive Python console over HTTP on any
  unhandled exception; on `0.0.0.0` that console was reachable from any
  network the host is on. Debug mode now requires `ETHIVIZ_ENV=development`
  explicitly; default host is `127.0.0.1`.
- `CORS(app)` allowed every origin on every route, including endpoints that
  return job results and list job history. Now restricted to
  `ETHIVIZ_ALLOWED_ORIGINS` (default `http://localhost:5173`, per this
  project's documented frontend port).
- The HTML export endpoint (`GET /api/analyze/results/<job_id>/export?format=html`)
  f-string-interpolated the raw analysis result — including user-uploaded
  text — into an HTML response with no escaping, so uploaded text containing
  `<script>` tags would execute in the exported report. Now `html.escape()`d.
- Added `MAX_CONTENT_LENGTH` (50MB) to reject oversized uploads outright
  instead of buffering them, and baseline response headers
  (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and a
  restrictive `Content-Security-Policy` on HTML responses).
- No authentication exists on any endpoint and no rate limiting is applied.
  This is unchanged in this pass — see "Known limitations" below.

## 0.6.0

Three phases of work on cultural-nuance detection: repairing metrics that were
structurally unable to measure what they documented, making multilingual
analysis real and honest about its own limits, and adding cross-cultural
reasoning at the dimension level.

Test suite: 81 → 162 tests.

### Breaking changes

- `calculate_intersectional_analysis()` returns `Dict[str, IntersectionResult]`
  instead of `Dict[str, float]`.
- `BuddhistLens`, `HinduLens`, `IndigenousLens` no longer accept a `registry=`
  keyword (it was accepted and silently unused).
- `cultural_inclusion_index()` returns a Jensen-Shannon similarity where it
  previously returned a key-overlap fraction. Existing thresholds are invalid.
- Scores shift across all seven lenses (severity weighting, negation guard,
  per-language calibration, blend renormalisation). Identical input yields
  different output.
- `iWEATAnalyzer.compound_effect` returns real values where it previously
  returned exactly `0.0` for every input.
- `RegulatoryMapper` triggers on worst-case rather than mean bias, so datasets
  that previously produced no obligations may now produce them.

**Migration:** any Platt calibration fitted under 0.5.0 (`scoring/
calibration_data/`) and any drift baselines (`scoring/drift_snapshots/`) are
invalid against 0.6.0 scores and must be refit, not carried forward.

### Fixed — metrics that could not measure what they claimed

- `DualEthicsFramework.resolve_conflict()` referenced bare names instead of
  `self.*` and raised `NameError` on every call. It had never worked.
- Intersectional analysis computed `score_a * score_b`, which is always less
  than or equal to either input, so it structurally inverted the compound
  disadvantage it documented. Rebuilt on a noisy-OR independence baseline with
  an amplification ratio that distinguishes superadditive (Crenshaw),
  independent, and buffered interactions.
- `cultural_inclusion_index()` ignored the reference distribution's values
  entirely — a balanced target and a 98/1/1 target both returned `1.0`. Rebuilt
  on Jensen-Shannon divergence over actual proportions.
- The iWEAT compound effect computed `actual - (axis1_effect + axis2_effect)`,
  which expands to zero for every possible input. The headline intersectionality
  metric was mathematically guaranteed to return `0.0`. Replaced with the
  difference-in-differences interaction term; the permutation test is now
  two-sided so negative interactions are detectable.
- `iWEATAnalyzer` measured association with an unnormalised dot product while
  `WEATAnalyzer` used cosine similarity, so the two disagreed on the same
  inputs and association strength was conflated with embedding magnitude.
- A `max()` over an empty sequence crashed dimension scoring in all seven
  lenses whenever `use_semantic=False`.

### Fixed — silent failure modes

- `_run_weat` swallowed every exception with a bare `except Exception: pass`,
  making a malformed word list indistinguishable from "no bias found". Failures
  are now logged and excluded explicitly.
- `run_iweat=True` assigned an empty dict; the public parameter silently did
  nothing. Now wired to real iWEAT execution.
- Regex patterns matched stereotypes being *quoted in order to refute them*
  ("the myth that African cultures are primitive" scored as biased). Added a
  shared negation guard across all seven lenses.
- Several patterns fired on bare topic-word co-occurrence rather than the
  harmful claim — "sustainably harvest timber from the forest" and "police
  vowed to prevent any attack on religious minorities" both scored as harms.
- `library_version` in provenance records read the *installed* distribution's
  metadata, so a record could name a different version than the source that
  produced it, or `"dev"` when run from a checkout.

### Multilingual

- Prototype translation coverage completed across all six supported languages;
  Buddhist, Hindu and Indigenous went from 0–70% to full coverage.
- Added per-language similarity calibration. The embedding model represents
  some languages coarsely enough that every sentence looks similar to every
  other, which inflated all dimensions uniformly — Hindi benign text scored
  0.72–0.82 across every dimension. Scores are now calibrated against each
  language's measured background similarity.
- The lexical (regex) channel exists only in English. It previously scored a
  structural `0.0` for other languages, deducting a flat 30% that read as "less
  biased" rather than "less measurable". The semantic channel is now
  renormalised to full weight when the lexical channel is unavailable.
- `LensScore` gained `analysis_coverage` and `warnings`; confidence now scales
  with how much of the pipeline actually applied instead of being a flat
  0.88/0.55. Degradation is reported through the API rather than to stdout.
- Language is detected per text rather than from `dataset[0]`, so a mixed
  corpus is no longer scored entirely in the first text's language.

### Added — dimension-level cross-cultural reasoning

- `frameworks/dimension_map.py` reads ten shared moral constructs beneath the
  per-lens scalars (e.g. Islamic `dignity_violation` and Hindu `dignity_harm`
  both express human dignity), reporting cross-tradition consensus and —
  critically — harms visible through only one tradition, which a single
  consensus score averages into invisibility.
- `ScoredResult.tradition_specific_findings()` and `.consensus_findings()`.
- WEAT word lists for `buddhist_v1`, `hindu_v1` and `indigenous_v1`; all seven
  lenses now produce suites (previously four, with three silently skipped).

### Lens parity and internals

- Buddhist, Hindu and Indigenous lenses gained dedicated per-category regex,
  tradition-weighted dimensions and specific recommendations, replacing a
  generic scorer that broadcast one undifferentiated regex hit across every
  dimension at equal weight.
- Prototype `severity` (hand-graded 0.60–1.00) was loaded but never used; it
  now scales each prototype's contribution.
- Conflict detection and synergy amplification extended to cover all seven
  lenses.
- Per-lens duplicated scoring and bootstrap code lifted into `EthicalLens`.
- Framework-level results now carry `peak`/`p90` alongside the mean, so
  concentrated harm is not diluted by corpus size.

### Testing

- The embedding mock returned an all-ones vector for every input, making cosine
  similarity exactly 1.0 for every pair. Lenses could not distinguish a matching
  prototype from an unrelated one, and assertions of the form "biased text
  scores high" passed without exercising the detector. Replaced with
  deterministic bag-of-words embeddings that preserve relative structure.
- Smoke tests asserting absolute thresholds (one asserted `> 0.5` on a
  dimension weighted `0.05`, unreachable legitimately) rewritten to assert
  structural properties that hold independent of embedding scale.

### Known limitations

- Prototype translations and non-English WEAT word lists are machine-generated
  and unreviewed. They are semantic anchors that directly determine scores, so
  a mistranslation silently corrupts every result in that language. Each file
  records this in a `translation_provenance` block; have a fluent reviewer
  confirm before treating non-English output as authoritative.
- All six supported languages are colonial/majority languages. The Indigenous
  lens cannot currently analyse text in the languages of the communities it
  exists to protect; adding those requires community partnership and
  CARE-aligned data governance, not machine translation.
- `compute_age_distribution` and `compute_gender_distribution` remain stubs.
- Calibrator and drift-monitor state is shared across requests on a
  process-wide `Analyzer`.
