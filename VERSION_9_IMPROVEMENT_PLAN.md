# EthiViz Version 9 Improvement Plan

## Purpose

Version 9 should move EthiViz from a safer, measured prototype toward an operationally
verifiable service. The focus is dependable job handling, evidence-based deployment
limits, clear data lifecycle behavior, and responsible presentation of analysis results.
V9 should improve the reliability of the system without implying that its cultural or
fairness scores are validated.

This plan now records the V9 implementation and its remaining evidence gates. V9 is a
separate snapshot based on [`Ethiviz_V8/README.md`](Ethiviz_V8/README.md), which documents
the preceding release.

## V9 implementation status

| Priority | Status | Delivered in V9 | Still open |
|---|---|---|---|
| 0 — Operating baselines | Partial | Added `Scripts/benchmark_api.py` for end-to-end text submission, queue delay when observable, execution, result retrieval, and machine-readable reporting. | No representative production measurements, image/mixed workload baselines, throughput/soak results, memory/CPU/GPU data, or capacity target has been established. |
| 1 — Job lifecycle | Partial | Added allowed terminal job transitions, persistent idempotency keys, queued-job cancellation, fail-closed configured Redis startup, and bounded local queue behavior. | Running work is intentionally not interrupted. Distributed cancellation races, worker/host restart recovery, and retry-exhaustion guarantees need deployment-level tests. |
| 2 — Retention and deletion | Partial | Added 168-hour upload cleanup and 720-hour terminal-job/result expiry, configurable retention, application deletion of uploads/results/idempotency mappings, and lower-detail failure audit entries. | Audit metadata remains, and backups, proxy/application logs, Redis persistence, and external copies are outside the application's deletion guarantee. Ownership and deletion must still be verified per deployment. |
| 3 — Deployment capacity | Partial | Added `/health/live`, `/health/ready`, explicit database/queue/worker checks, and startup failure when a configured Redis backend is unavailable. | No production reference profile, measured resource limits, overload/soak tests, outage drills, or operational dashboards are claimed. |
| 4 — Interface clarity/accessibility | Partial | Added a queued cancellation control and live announcements for progress and terminal cancellation. | Full keyboard-only workflow, screen-reader/chart alternatives, contrast audit, automated accessibility CI, and manual assistive-technology review remain open. |
| 5 — Governed evaluation | Deferred | Preserved the existing limitations and governance requirements; no evaluation data was fabricated. | Community partnership, consent, qualified human review, adjudication, held-out evidence, and approval of any validity claim remain prerequisites. |

These are implementation-status notes, not a production-readiness declaration. The V9
README, changelog, compliance notes, and test suite are authoritative for current
behavior; any acceptance criterion above that remains open is not represented as complete.

## Guiding principles

- Measure a representative workload before setting performance or capacity targets.
- Preserve existing API behavior unless a versioned change is necessary; document any
  migration and compatibility impact.
- Treat job status, retries, cancellation, and deletion as observable lifecycle
  behaviors, not best-effort promises.
- Do not log raw user content, credentials, or other sensitive values for debugging or
  metrics.
- Keep analysis outputs exploratory decision-support signals. Do not claim accuracy,
  fairness certification, cultural validity, or suitability for consequential decisions
  without independent evidence and appropriate governance.
- Community consent and qualified human review are prerequisites for promoting cultural
  prototypes or translations beyond draft status.

## Priority 0 — Establish end-to-end operating baselines

### Work

- Extend the existing benchmark beyond direct engine execution to include API submission,
  queue delay, worker execution, result retrieval, and export.
- Define representative, non-sensitive test workloads for text, images, mixed jobs,
  supported languages, and repeated inputs. Record workload characteristics without
  storing the input content in benchmark output.
- Measure cold start, queue wait, execution p50/p95, throughput, peak memory, failure
  rate, retry rate, and recovery time for the supported local and Redis/RQ deployment
  modes.
- Record environment and configuration needed to compare runs: code revision, Python and
  Node versions, model identifiers, worker count, backend, cache state, and hardware.
- Establish targets only after collecting repeatable reference results. Keep engine
  execution time distinct from queue wait and total user-visible time.

### Acceptance criteria

- Benchmark output is machine-readable, repeatable, and labels unmeasured values as
  unavailable rather than estimating them.
- A documented baseline covers both SQLite/local queue and the recommended production
  queue/database configuration, or explicitly identifies any unsupported combination.
- Every performance claim is tied to workload, environment, sample count, and a
  baseline comparison; no target is met by silently reducing analysis coverage.

## Priority 1 — Make queued job lifecycle dependable

### Work

- Specify and enforce allowed job-state transitions, including behavior when a worker
  crashes or a client retries a submission.
- Add cancellation with clear semantics for queued and running work. If an operation
  cannot be interrupted safely, report cancellation as pending or unavailable rather
  than claiming it stopped.
- Add an idempotency mechanism for submission retries so transient client/network errors
  do not create duplicate jobs or duplicate side effects.
- Make retry behavior explicit and bounded; clean up temporary files and partial outputs
  after failure, cancellation, timeout, and restart.
- Exercise graceful shutdown and recovery for in-process and Redis/RQ workers. Define
  which jobs resume, fail, or require resubmission after a process or host restart.
- Expose queue saturation and worker health using metrics that do not contain job text,
  filenames, API keys, or user identifiers.

### Acceptance criteria

- Tests cover each valid and invalid state transition, duplicate submission, queued and
  running cancellation, worker termination, retry exhaustion, and cleanup.
- A client can distinguish completed, failed, cancelled, and still-running work without
  relying on undocumented status values.
- Recovery tests verify that jobs and artifacts are neither silently lost nor processed
  twice after a worker restart.
- Queue overload returns documented backpressure and does not create unbounded in-memory
  work.

## Priority 2 — Verify data retention and deletion end to end

### Work

- Inventory where job inputs and outputs can persist: upload directories, job stores,
  queue backends, application and proxy logs, exports, temporary files, and backups.
- Define separate retention periods and deletion responsibilities for each location.
  Distinguish application deletion from backup expiry or deletion in external systems.
- Implement or verify scheduled cleanup for expired uploads, stale job records, and
  temporary artifacts; make the effective policy configurable and visible to operators.
- Test authorized deletion for SQLite and PostgreSQL-backed stores, including related
  files and audit records. Preserve only the minimal audit information required by the
  documented policy.
- Review logs and error responses for accidental input, secret, and personal-data
  exposure.
- Update the compliance and deployment documentation to match behavior verified by tests,
  including any limits on deletion guarantees.

### Acceptance criteria

- Retention behavior is stated per storage location, with configuration names, defaults,
  cleanup timing, and operator responsibilities.
- Tests demonstrate deletion of the job record and application-managed artifacts, and
  demonstrate that another caller cannot read or delete the job.
- Backup and third-party retention limitations are disclosed; the application does not
  claim to erase copies it cannot control.
- Automated checks ensure representative sensitive values do not appear in logs,
  metrics, or error responses.

## Priority 3 — Define and validate safe deployment capacity

### Work

- Publish a reference deployment profile with tested worker count, queue depth, timeout,
  memory use, and dependency versions, derived from Priority 0 measurements.
- Add readiness and health signals that distinguish API availability, database
  connectivity, queue availability, and worker availability.
- Document behavior during database, Redis, worker, disk-space, and model-load failures;
  return actionable operator errors without exposing internal details to callers.
- Add bounded-duration load and soak tests for the supported production stack, including
  overload, worker restart, and dependency outage scenarios.
- Validate that container and documented bare-metal deployment settings use the same
  authentication, origin, TLS/proxy, and security-header assumptions.
- Keep secrets out of images, logs, metrics, and example configuration; document
  rotation and revocation procedures.

### Acceptance criteria

- A deployment guide names the tested profile and its measured limits rather than
  recommending an unverified worker count.
- Health checks identify dependency failures accurately and do not report readiness when
  a required queue or database is unavailable.
- Load tests show bounded resource use and predictable backpressure at and above the
  documented profile.
- Operational dashboards or metric queries distinguish queue delay, job execution, error
  rate, retries, and worker health without exposing sensitive labels.

## Priority 4 — Improve clarity, accessibility, and recovery in the interface

### Work

- Audit core workflows for keyboard use, semantic structure, focus management, contrast,
  accessible names, and screen-reader announcements.
- Make submission progress and terminal job states understandable, including timeout,
  cancellation, retryable failure, and how to recover.
- Present score meaning, coverage limitations, warnings, and uncertainty alongside
  results; do not use visual severity or confidence indicators in a way that suggests
  independently validated certainty.
- Ensure large or partial results remain navigable and exports retain the same
  caveats and provenance shown in the interface.
- Add regression coverage for loading, empty, partial, error, and completed states,
  including deferred visualization chunks.

### Acceptance criteria

- The primary submit-to-results workflow can be completed using keyboard-only input.
- Automated accessibility checks run in CI for the main application surfaces, and
  documented manual checks cover screen-reader announcements and chart alternatives.
- Job errors and states provide the same user-action guidance in the UI and API.
- Every exported report preserves the limitations, warnings, and provenance that qualify
  its analysis.

## Priority 5 — Govern evaluation and cultural-content changes

### Work

- Define an evaluation protocol before collecting or labeling material: intended use,
  scope, consent, reviewer qualifications, adjudication, held-out data, and withdrawal
  process.
- Partner with relevant language and cultural communities before treating translations,
  prototypes, or examples as reviewed. Preserve provenance at the bundle and entry level.
- When a consented, qualified human-reviewed set is available, report results by lens,
  language, and relevant input domain, with reviewer disagreement and uncertainty.
- Add controlled regression comparisons for changes to prototypes, thresholds, models,
  and scoring. Review potentially harmful changes before release.
- Keep group-fairness metrics and mitigation workflows out of default product claims
  unless valid group labels, task outcomes, consent, and methodological review exist.

### Acceptance criteria

- Evaluation findings include data provenance, consent and use terms, reviewer process,
  limitations, and uncertainty; synthetic or machine-translated labels are not described
  as ground truth.
- No accuracy, calibration, fairness, or cultural-validity claim is added without
  appropriate held-out evidence and review.
- Prototype and model changes have a reproducible before/after report and a documented
  approval decision; missing evidence blocks promotion rather than being represented as
  a successful validation.

## Recommended delivery sequence

1. **Specify and measure:** agree on workload definitions and collect end-to-end
   baselines before setting targets.
2. **Harden job lifecycle:** implement state, idempotency, cancellation, cleanup, and
   recovery semantics, with failure-injection tests.
3. **Prove data lifecycle:** verify deletion and retention across application-managed
   stores and document external backup boundaries.
4. **Validate deployment capacity:** test a documented production profile under load,
   dependency failure, and restart conditions.
5. **Improve user operation:** address accessibility and explain job progress, errors,
   limitations, and recovery consistently.
6. **Advance evidence when governance permits:** conduct community-informed evaluation
   and only then consider evidence-backed score or validity claims.

Priorities 0–3 are release-readiness work for claims about performance, reliability, and
data handling. Priority 4 improves safe use but does not establish analytical validity.
Priority 5 depends on consent, qualified reviewers, and community partnership; it must
not be replaced by synthetic data or schedule pressure.

## Explicitly out of scope until evidence exists

- Promising a specific accuracy, fairness, or cultural-validity level based on current
  heuristic scores.
- Enabling group-fairness or mitigation workflows without valid, consented group labels
  and task outcomes.
- Treating machine translation or unreviewed prototypes as community-approved content.
- Claiming complete erasure from backups, proxies, or external infrastructure that
  EthiViz does not control.
- Increasing concurrency, cache retention, or resource limits without measurements and
  regression evidence.

## Release gate

A V9 release should ship only the work that has passed its stated acceptance criteria.
The release notes should distinguish implemented and tested behavior from deferred work,
include measured deployment limits where available, and retain the current product
limitations in the UI, API documentation, and exports.
