# EthiViz V5: Safety, Scalability & Production-Readiness Plan for Public Launch

## Context

EthiViz V4 (`/home/brandon/Documents/brandon/Ethiviz/Ethiviz_V4`) is an alpha-stage
Python package (`pyproject.toml` lists `Development Status :: 3 - Alpha`, v0.5.0)
implementing cross-cultural AI bias/fairness detection across 7 ethical traditions,
built on the author's bachelor's thesis. It works as a library today. The user wants
to take it public and asked specifically for a plan — no code — covering safety/
guardrails, scalability, and production readiness.

Direct code inspection (confirmed by two independent passes, plus manual verification
of the highest-stakes claims) shows EthiViz is currently a research prototype with a
genuine product underneath it, but with one blocking structural problem and several
launch-blocking safety gaps that sit *outside* normal web-security hardening, because
the product itself performs biometric/demographic inference on images of real people.
This plan sequences the work so nothing is hardened, scaled, or shipped before the
things that would make that unsafe or premature are resolved first.

---

## Key finding: there is no working end-to-end product yet (Phase 0 blocker)

Three independent, mutually incompatible "backend" implementations exist, and the one
real, working frontend lives **outside this repo**:

- `ethiviz/server.py` — the only one that actually runs. Synchronous Flask app,
  routes `/`, `/analyze/text`, `/analyze/image`, `/stop`, `/health`. No job concept.
- `run_platform.py` — a separate, abandoned FastAPI prototype (port 8080) with a
  **faked** image-analysis endpoint (`await asyncio.sleep(2)` then a hardcoded
  "Face detected... Type II" string regardless of the uploaded image).
- README.md and `start.sh`'s printed banner both document a third API shape —
  `POST /api/analyze` → `job_id`, polling via `/api/analyze/status/{job_id}` — backed
  by `ethiviz/storage/job_store.py` (a real SQLite jobs/results/audit_log schema).
  **The server code that implements this (`Scripts/api_server.py`) does not exist
  anywhere in the V4 tree.** `job_store.py` is unused scaffolding.
- `Ethiviz_V4/project/` (the frontend README tells users to `npm run dev`) contains
  only 4 orphaned `.tsx` files — no `package.json`, no `vite.config`, no `index.html`.
  It cannot run.
- The **only working frontend** is a sibling repo, `/home/brandon/Documents/brandon/Ethiviz/project/`,
  and it's built entirely against the async job-queue API that was never implemented
  in V4 (`ConfigPanel.tsx` expects a 202 + `job_id`/`status_url` response).
- `Flask`/`flask-cors` and `FastAPI`/`uvicorn` are used in the two server files but are
  **not declared as dependencies anywhere** in `pyproject.toml`.

Net effect: none of the safety, scaling, or hardening work below has a stable target
to land on until one canonical backend + frontend pair is chosen and made to actually
work end-to-end. This has to be Phase 0, ahead of everything else.

---

## Phase 0 — Architecture reconciliation (prerequisite for all other work)

1. Decide the one canonical architecture: adopt the documented async job-queue design
   (finish wiring `ethiviz/storage/job_store.py` to a real server) since a real
   frontend (`Ethiviz/project/`) is already built against that contract, rather than
   against the sync `ethiviz/server.py`.
2. Consolidate to a single repo/source of truth: migrate the working frontend
   (`Ethiviz/project/`) into `Ethiviz_V4/project/`, retire the orphaned `.tsx` stubs,
   retire `run_platform.py` entirely, and rewrite the README/`start.sh` banner to
   match what actually ships.
3. Add `flask`, `flask-cors` (or whatever framework Phase 0 lands on), and their
   ASGI/WSGI server to `pyproject.toml` as real dependencies.
4. Treat the wider workspace sprawl as part of this step: `Ethiviz_V2/`, `Ethiviz_V3/`,
   `Blitzy_Ethiviz/`, loose scripts and result JSON files sitting in the parent
   `Ethiviz/` directory need a one-time decision (archive vs. delete vs. fold in)
   before "V4" can be called the product's source of truth. Nothing here should be
   deleted without your explicit sign-off per file/folder.

Exit criterion: one backend, one frontend, one documented API contract, a person can
clone the repo and get a real upload → real analysis → real result round-trip.

---

## Phase 1 — Must-fix before any public exposure (safety-critical, non-negotiable)

These are launch-blocking regardless of how few users see it on day one — a single
early adopter uploading one real photo is enough to trigger the exposure below.

### Safety / guardrails (the unusual risks specific to this product)

- **Biometric categorization legal review.** `ethiviz/vision/skin_tone.py`
  (ITA/Fitzpatrick estimation) + `ethiviz/vision/face_detector.py` (MediaPipe) +
  `ethiviz/vision/cultural_element_detector.py` (CLIP zero-shot religious/cultural
  symbol detection) together infer race-adjacent and religion-adjacent attributes from
  images of real, identifiable people. This is squarely the kind of processing the EU
  AI Act (Art. 5(1)(b)) restricts. Get explicit legal review of whether/how this can
  be offered as a public service — especially to EU users — before opening image
  upload to the public. This is a go/no-go gate, not a documentation task.
- **CSAM-reporting obligation.** Any public image-upload endpoint carries a real,
  standard legal/operational obligation in most jurisdictions to detect and report
  CSAM. Decide the operational plan (scanning provider, reporting workflow, retention
  of evidence) before public image upload goes live — this is not optional hardening.
- **Structural (not just README) disclaimers**, shown with every result, covering
  three distinct things that currently only have one weak analog (the regulatory
  disclaimer in `ethiviz/context/regulatory.py`, "informational only, not legal
  advice"): (a) bias/fairness scores are decision-support signals, not proof of
  fairness or bias in a legal/HR sense; (b) the 7-lens framework (`ethiviz/lenses/*`,
  `ethiviz/frameworks/builtin/*.yaml`) is one researcher's operationalization of these
  traditions for research purposes, not an authoritative or scholar-endorsed
  representation of Ubuntu/Confucian/Islamic/Buddhist/Hindu/Indigenous ethics; (c)
  image-analysis outputs (skin tone, cultural-element detection) are estimates with
  known error margins, not identity claims.
- **Fairness-washing mitigation.** Nothing today stops someone from cherry-picking
  the most favorable lens/tradition and citing "analyzed with EthiViz" as fairness
  proof. Decide a product/ToS stance — e.g., discourage or disable exporting a
  single-lens result as a standalone "certificate"; encourage full 7-lens export as
  the only citable artifact.
- **Abuse/content policy for uploads**: what happens when someone uploads hate speech,
  CSAM, or other harmful content for "analysis" — decide moderation, logging-for-abuse-
  investigation vs. privacy-preserving retention (these two goals conflict; pick
  deliberately), and file-type/content validation before this is public.

### Production readiness (minimum viable hygiene)

- Remove or authenticate the `/stop` endpoint — currently unauthenticated and calls
  `os._exit(0)` (`ethiviz/server.py:210-227`), a trivial one-request DoS. The same
  unauthenticated-stop pattern exists independently in `run_platform.py`, so this is a
  recurring habit to fix at the source, not a one-off patch.
- Set `MAX_CONTENT_LENGTH` on the Flask app — currently unbounded upload size.
- Lock CORS to real production origins (currently hardcoded to `localhost:5173`/`5000`).
- Fix silent exception-swallowing in upload parsing (`server.py:110-121`, bare
  `except Exception: texts = [content]`) — replace with real validation and a real
  error response.
- Guard against `--debug` ever being set in a deployed environment (Flask debug mode
  + a non-localhost host is remote code execution via the Werkzeug debugger).
- Add basic structured logging (currently zero `logging` usage anywhere in `ethiviz/`,
  only `print()`) and minimal error tracking — you need *some* visibility into what a
  public launch is doing before it's public.
- **Resolve shared mutable state in `Analyzer`.** `ethiviz/api.py:61-62` sets
  `self.calibrator = PlattCalibrator()` and `self.drift_monitor = DriftMonitor()` as
  per-instance state, but `ethiviz/server.py` holds one process-wide singleton
  `_analyzer` shared across all concurrent Flask request threads. `drift_monitor
  .record_snapshot(...)` (called on every `analyze()`, see `ethiviz/scoring/drift.py`)
  accumulates score-distribution history *across unrelated users' requests* — this is
  both a race condition and a cross-tenant data-contamination risk (one user's inputs
  can influence calibration/drift state that shapes another user's results). Decide
  deliberately: either isolate calibrator/drift state per request or session, or — if
  population-level drift monitoring across all users is actually the intended design —
  document and scope that explicitly rather than leaving it as an accident of a
  global singleton.

---

## Phase 2 — Needed for scale (should be near-ready by launch, can trail a soft launch)

- Implement the async job-queue for real: wire the already-designed
  `ethiviz/storage/job_store.py` schema (jobs/results/audit_log) to an actual task
  queue (Celery/RQ/arq) rather than reinventing it — the schema is sound, it's just
  never been connected to a worker.
- Split worker pools by workload: text analysis (light — numpy/pandas/sklearn) vs.
  image analysis (heavy — `vision` extra pulls in torch, transformers, mediapipe,
  opencv; a multi-GB container). These have very different scaling/cost profiles and
  should scale independently, with image workers scaled down more aggressively given
  likely lower volume.
- Pin ML model downloads. `cultural_element_detector.py` pulls
  `CLIPModel.from_pretrained("openai/clip-vit-base-patch32")` from the HuggingFace Hub
  at runtime with no revision pin (same likely applies to sentence-transformers and
  Stanza language models under the `multilingual` extra). This is both a cold-start-
  latency problem per worker and a supply-chain integrity problem — pin and
  bake/cache weights into the deployment artifact instead of pulling at request time.
- Define the retention/deletion policy for `job_store.py`'s `results`/`audit_log`
  tables *before* wiring it up for real traffic — once it holds real user-submitted
  content (including image-derived biometric inferences), retention is a privacy
  requirement, not a scaling nice-to-have. Design this before Phase 2 wiring, not after.
- Dockerize the chosen Phase-0 architecture; add CI (GitHub Actions) to actually run
  the existing `pytest.ini` suite on every PR — right now it exists but nothing
  invokes it automatically (`.github/` only contains a Codacy instructions file for an
  AI assistant, not a workflow).
- Add dependency/vulnerability scanning given the heavy ML dependency surface
  (torch/transformers have real CVE history) — e.g., Dependabot or `pip-audit` in CI.

---

## Phase 3 — Post-launch hardening (nice-to-have, not launch-blocking)

- API-layer test coverage: all current tests (`test_smoke.py`, `test_v4_upgrades.py`,
  `test_v5_tier4.py`) exercise library/scoring logic only — zero tests touch
  `server.py`'s routes. Add these alongside the Phase 1 server fixes so there's a
  regression safety net, not after.
- Load testing, full observability/metrics dashboards, formal `SECURITY.md` and a
  vulnerability-disclosure channel (so researchers have somewhere to report issues
  instead of a public GitHub issue or social media).
- Expanded auth (SSO/roles) if multi-user/team features are added later.
- License compliance pass across the heavy optional extras (e.g., some Stanza
  language models carry non-commercial licenses) before bundling them into a
  commercial "full" install offering.

---

## How the phases/pillars interlock (why this order, specifically)

- **Phase 0 blocks everything**: you cannot secure, scale, or productionize an
  integration between a frontend and backend that don't actually speak the same
  protocol today. Auth, rate limiting, and logging all need one stable target to land
  on, and the sync-vs-async decision changes what "scaling" even means here.
- **Safety (Phase 1) is independent of scale** — the biometric-categorization and
  CSAM-obligation items are launch-blocking at any traffic volume, including zero.
  Don't let scale/production polish delay resolving these; conversely, don't let
  these become an excuse to delay basic production hygiene (auth, logging) either —
  do both in Phase 1.
- **Production hygiene must precede scale work**: adding a job queue and worker pools
  on top of a server with an unauthenticated kill-switch and no logging means scaling
  something you can't operate or debug. Phase 1 production items land before Phase 2
  scale items.
- **Retention policy sits at the safety/scale intersection**: it must be designed
  before `job_store.py` is wired up for real traffic (a Phase 2 action), because once
  it persists real user content the retention decision becomes a privacy requirement,
  not an afterthought.

---

## Verification approach (once this plan moves into execution)

Since this document is planning-only, verification isn't part of this deliverable —
but for reference when execution begins: Phase 0 exit is verified by a real upload →
analysis → result round-trip through the browser; Phase 1 items are verified by
targeted API tests (currently absent) exercising `server.py`'s routes plus a manual
pass confirming `/stop` requires auth, oversized uploads are rejected, and debug mode
cannot be enabled in a non-localhost deployment; Phase 2 items are verified by load
testing the job queue and confirming worker pools scale independently.
