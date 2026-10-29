# EthiViz Version 10 Improvement Plan

## Purpose

V10 should turn V9's implemented operational controls into deployment evidence and a
governed operating model. It should not expand analytical claims or concurrency limits
until representative testing, qualified review, and community governance support them.
This plan is a proposal, not a statement that V10 work is implemented, funded, or
scheduled.

V9 added persistent idempotency, job-state enforcement, queued-only cancellation,
fail-closed Redis configuration, health/readiness endpoints, application retention
defaults, an API-level benchmark, and accessible status announcements. Its remaining
gaps are recorded in the [V9 plan](VERSION_9_IMPROVEMENT_PLAN.md) and
[V9 README](Ethiviz_V9/README.md).

## Guiding principles

- Base deployment limits and service objectives on repeatable, representative
  measurements; do not infer capacity from a successful build or a single smoke test.
- Keep text, images, mixed workloads, queue delay, engine execution, and end-user latency
  separately measurable.
- Treat consent, reviewer qualifications, community partnership, and withdrawal/correction
  processes as prerequisites for evaluating or promoting cultural content.
- Preserve explicit uncertainty and limitations in the UI, API, exports, and release
  decisions; do not convert screening scores into validated fairness claims.
- Make data-retention boundaries visible, including the systems EthiViz does not operate.

## Priority 0 — Establish a production-representative capacity profile

### Work

- Run the V9 API benchmark against the exact supported local and production topologies,
  including Redis/RQ and PostgreSQL where supported.
- Define consented, non-sensitive workload profiles for text, images, mixed jobs,
  language mixes, job sizes, cold/warm model state, and repeated inputs.
- Measure queue wait, execution, retrieval/export latency, throughput, peak memory,
  CPU/GPU utilization, failure/retry rate, disk use, and recovery time with sample counts
  and environment metadata.
- Exercise saturation, overload/backpressure, Redis/database outage, worker loss, and
  process restart; publish limits only for tested configurations.
- Keep resource and queue measurements separate from analysis quality and score
  equivalence.

### Acceptance criteria

- Reports are machine-readable, repeatable, versioned, and do not contain raw user input.
- Each supported deployment profile has repeated measurements and an explicit tested
  worker count, queue capacity, timeout, and resource envelope.
- Unmeasured fields remain unavailable; SLOs and capacity claims cite workload,
  environment, sample count, and uncertainty.
- Overload and dependency failures have bounded, tested behavior without silent job loss.

## Priority 1 — Prove lifecycle recovery and cancellation semantics

### Work

- Test every job transition and submission-retry path under concurrent requests against
  both SQLite/local queue and PostgreSQL/Redis/RQ.
- Define durable semantics for queued, running, retrying, failed, cancelled, and
  abandoned jobs after API/worker termination.
- Keep running-job cancellation unavailable unless the engine can cooperatively stop
  work and clean up safely; if cooperative cancellation is added, expose its state and
  terminal result without claiming success prematurely.
- Verify retries do not duplicate results or side effects and that idempotency behavior
  is consistent across process restarts and job deletion.
- Exercise graceful shutdown, worker restarts, dead-letter/failure handling, and cleanup
  of partial files/results.

### Acceptance criteria

- Failure-injection tests cover worker termination before, during, and after persistence,
  queue retries, duplicate submissions, and concurrent cancellation.
- Each status and cancellation response reflects durable state and clearly distinguishes
  queued cancellation from work that is running or cannot be stopped.
- Recovery behavior is documented and tested for every deployment profile; unsupported
  behavior is explicitly identified.

## Priority 2 — Verify the complete data lifecycle

### Work

- Build a deployment-specific data-flow inventory for uploads, job records/results,
  audit events, idempotency digests, queues, exports, temporary files, logs, backups,
  reverse proxies, and external services.
- Define retention periods, access controls, deletion responsibilities, and audit
  retention for every store. Include backup expiry and restore behavior.
- Add authorized deletion/expiry tests for SQLite and PostgreSQL, proving another API
  key cannot read, cancel, export, or delete a job.
- Review logs, metrics, tracing, and errors for filenames, secrets, identifiers, and
  sensitive input. Define handling for incidents and data-subject requests.
- Make `GET /health/ready`, queue worker-health reporting, and operator errors consistent
  across direct and reverse-proxy deployments.

### Acceptance criteria

- A reviewed retention schedule maps each data store to a configuration/default, cleanup
  timing, accountable operator, and deletion limitation.
- Automated tests verify application-managed deletion and ownership isolation; backup,
  proxy, Redis, and third-party deletion are documented with evidence from their operators.
- Representative sensitive values do not appear in newly generated logs, metrics, or
  API errors.
- Restore and expiry tests establish whether retained backups can reintroduce deleted
  application data and how that risk is handled.

## Priority 3 — Complete accessibility and human-oversight validation

### Work

- Audit keyboard navigation, focus order and restoration, names/roles, contrast, zoom,
  screen-reader announcements, error recovery, and chart equivalents in the full
  submit-to-results/export workflow.
- Add automated accessibility checks to CI and document manual checks with representative
  assistive technologies.
- Ensure that partial, failed, cancelled, and timed-out jobs have clear recovery guidance.
- Keep explanatory caveats, uncertainty, limitations, and provenance visible alongside
  results and in all export formats.

### Acceptance criteria

- The core workflow passes documented keyboard-only and screen-reader review.
- CI flags new accessibility regressions on primary app surfaces.
- Charts and visual indicators have text alternatives that preserve meaning without
  implying certainty or validation.
- UI, API, and exported reports use consistent job-state and human-review guidance.

## Priority 4 — Establish AI governance and evaluation evidence

### Work

- Name accountable system, deployment, privacy/security, release, evaluation, and
  community/data-governance owners; maintain a deployment-specific system record and
  impact/risk assessment.
- Establish a consented, community-informed evaluation protocol with intended use,
  reviewer qualifications, adjudication, held-out data, uncertainty reporting, and
  correction/withdrawal procedures.
- Review prototype and translation provenance for every tradition/language, preserving
  the distinction between machine-generated, pending, reviewed, and community-authorized
  material.
- Add controlled before/after regression review for changes to prototypes, thresholds,
  models, dependencies, and user-facing claims.
- Create an incident/reporting, pause/rollback, correction, and release-approval process.

### Acceptance criteria

- No accuracy, calibration, fairness, or cultural-validity claim is made without
  independently reviewed held-out evidence and documented limitations.
- Cultural content is not promoted based solely on machine translation or synthetic
  labels; consent and reviewer evidence are auditable.
- Release decisions record intended use, risk owners, evidence, open actions, and
  residual-risk acceptance.

## Recommended delivery sequence

1. Agree on the supported deployment profiles and collect repeatable capacity baselines.
2. Run lifecycle and outage failure-injection tests on those profiles.
3. Reconcile all application and infrastructure retention/deletion responsibilities.
4. Complete accessibility testing and align UI/API/export recovery language.
5. Establish accountable AI governance and community-informed evaluation before making
   analytical validity claims.

Priorities 0–3 improve measurable service operation but do not validate analysis quality.
Priority 4 depends on qualified reviewers, community partnership, consent, and
deployment-specific governance; it must not be bypassed to meet a release date.

## Explicitly out of scope until evidence exists

- Publishing unmeasured worker counts, throughput, latency SLOs, or resource limits.
- Claiming running-job cancellation or restart recovery beyond tested behavior.
- Claiming complete erasure from infrastructure or backups controlled by other operators.
- Treating machine-translated or unreviewed content as community-approved ground truth.
- Using EthiViz scores alone for consequential decisions or representing them as
  independent fairness certification.

## Release gate

A V10 release may claim only behavior demonstrated by tests and deployment evidence.
Any unmet acceptance criterion must be listed as deferred, with an owner and an explicit
restriction on the associated product or operational claim.
