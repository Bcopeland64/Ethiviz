# EthiViz AI Governance Assessment

**Assessment date:** 2026-10-28
**System reviewed:** EthiViz V8 repository snapshot
**Assessment type:** Documentary and source-code desk review
**Overall conclusion:** Governance controls are partially evidenced. The project
documents important limitations and implements several useful operational safeguards,
but material governance and assurance gaps remain. The repository alone does not support
claims of validated cultural/fairness performance, regulatory compliance, or readiness
for consequential use.

## V9 implementation update — 2026-10-29

This supplement reviews repository changes in `Ethiviz_V9/` against the V8 findings below.
It is a source/document/test review only; the V8 assessment scope limitations still apply.
No live deployment, production configuration, Redis/PostgreSQL recovery, backup schedule,
community partnership, human evaluation, or legal context was independently verified.

**New repository evidence:** V9 adds persistent idempotency records, allowed job-state
transitions, queued-only cancellation, failure-closed Redis configuration, database/
queue/worker readiness checks, configurable application upload and terminal-job
retention, an API-level benchmark, and basic live-region announcements. The V9 plan
identifies each as partial where production or external evidence remains missing.

**Updated posture:** These changes improve operational transparency but do not establish a
production capacity profile or complete recovery/deletion guarantees. Cancellation is
not available once a job is running. V9 retains audit metadata after deletion, and the
application cannot erase copies in backups, proxies, Redis, or external systems.
Accessibility changes are not a complete conformance audit. No qualified,
consented, human-reviewed evaluation corpus or community authorization was added.

**Governance conclusion:** The V8 High findings concerning accountable deployment
ownership, cultural provenance/consent, governed evaluation, and use-context assessment
remain open. V9 offers partial implementation evidence for retention/queue configuration
and limited accessibility behavior, but the repository still does not support claims of
validated cultural/fairness performance, regulatory compliance, or readiness for
consequential use. See the [V9 plan](../VERSION_9_IMPROVEMENT_PLAN.md) and
[V9 action status](Action_Register.md).

## 1. Executive summary

EthiViz analyzes text and images using seven ethical-tradition lenses and presents
decision-support signals. The V8 README appropriately characterizes outputs as
exploratory and states that they are not validated fairness certifications or substitutes
for domain expertise and community review. It also discloses that no qualified,
consented, human-reviewed evaluation corpus is included and that backups and some
deployment-specific retention remain outside the application's verified guarantees.

The repository shows positive controls: API authentication can be enabled and unsafe
non-loopback binding is rejected without it; job ownership checks exist; uploads and
queues are bounded; analysis warnings and translation-review status can reach results;
audit logging and deletion endpoints exist; and CI runs backend/frontend tests, a
production dependency audit, and a frontend bundle budget.

However, a governance program cannot be inferred from code safeguards alone. The
repository does not establish accountable AI-system owners, a deployment-specific
impact/risk assessment, or a complete operating lifecycle for monitoring, incidents,
human oversight, and change approval. Translation provenance and consent controls are
not consistently evidenced across prototype bundles. Retention documentation is
outdated relative to V8 and does not establish end-to-end deletion. Human-reviewed
performance and cultural-validity evidence is absent. Some implementation behaviors
also deserve explicit operator review, including legacy jobs with no owner being
accessible to any authenticated caller and Redis initialization failures falling back
to an in-process queue.

**Recommended decision:** Continue controlled development and low-risk exploratory
pilots with explicit user-facing limitations. Before external or consequential use,
close the high-priority actions in the [Action Register](Action_Register.md), validate
the exact deployed configuration, and obtain qualified legal, technical, and community
review appropriate to the use case.

## 2. Scope, evidence, and limitations

### In scope

- V8 product description, limitations, and validation instructions in
  [`Ethiviz_V8/README.md`](../Ethiviz_V8/README.md).
- Prototype governance and compliance documents:
  [`data_governance.md`](../Ethiviz_V8/docs/data_governance.md) and
  [`compliance.md`](../Ethiviz_V8/docs/compliance.md).
- Selected API, queue, job-store, prototype, scoring/evaluation, frontend, CI, and test
  implementation in `Ethiviz_V8/`.
- The existing V9 improvement proposal in
  [`VERSION_9_IMPROVEMENT_PLAN.md`](../VERSION_9_IMPROVEMENT_PLAN.md), as contextual
  evidence of acknowledged next-version gaps.

### Not in scope

- Live or production deployment, cloud accounts, infrastructure-as-code, access logs,
  backup schedules, incident records, or vulnerability testing.
- Interviews with developers, operators, users, reviewers, or communities.
- Independent statistical evaluation of model outputs or translations.
- Legal classification or compliance conclusions for a particular sector, jurisdiction,
  or deployment.
- Certification, formal ISO/IEC 42001 clause-by-clause audit, or organizational
  management-system effectiveness.

### Method

The review uses a qualitative evidence scale:

- **Evidenced:** Documentation and/or implementation provides observable evidence of
  the control.
- **Partially evidenced:** A control exists in part, but scope, enforcement, consistency,
  or operating evidence is incomplete.
- **Not evidenced:** The reviewed repository did not provide sufficient evidence. This
  does not prove that the control does not exist outside the reviewed material.

Severity is a prioritization judgment for governance follow-up, not a vulnerability
rating or a formal risk calculation:

- **High:** A gap could materially undermine rights, safety, privacy, cultural
  legitimacy, or the reliability of deployment decisions if the system is used externally
  or consequentially.
- **Medium:** A meaningful weakness that should be resolved or explicitly accepted by an
  accountable owner before broader operationalization.
- **Low:** Improvement that strengthens consistency, evidence, or usability but is not
  by itself a release blocker for a tightly controlled exploratory pilot.

The themes are informed by AI management-system and AI risk-management practices,
including accountability, intended-use context, risk treatment, data governance,
measurement, transparency, and lifecycle monitoring. This is not a claim that the
repository has been assessed against every requirement of any standard.

## 3. System context and intended use

The V8 README describes a tool that analyzes text and images across Western, Ubuntu,
Confucian, Islamic, Buddhist, Hindu/Dharmic, and Indigenous/First Nations traditions.
It frames results as exploratory decision-support signals and warns against treating
them as legal determinations, validated certifications, or substitutes for experts and
community review.

The system includes an analysis engine, a Flask API, persistent job handling, optional
Redis/RQ processing, a React/Vite interface, exports, and optional computer-vision
components. Inputs may include uploaded text files and images. Results include
tradition-level scores, confidence/coverage information, warnings, and derived
visualizations.

The reviewed documentation does not define one specific deployed context, user
population, decision workflow, data-controller/operator relationship, or consequence
level. Those details determine applicable risk controls and legal obligations and must
be established by each deployer before use.

## 4. Governance findings

### G-01 — Accountable governance roles and lifecycle controls are not evidenced

**Severity: High | Evidence status: Not evidenced**

The V8 materials describe engineering controls and product limitations, but the reviewed
V8 documentation does not identify accountable roles for system ownership, risk
acceptance, data stewardship, incident response, release approval, or community
engagement. No V8-specific AI-system inventory, deployment impact assessment, risk
acceptance record, or incident/escalation process was found in the reviewed materials.
General project-management risk and governance documents exist elsewhere in the
repository, but their applicability to the current V8 AI system and its operation is not
established by this review.

**Why it matters:** Technical controls do not establish who decides whether residual risk
is acceptable, who responds when outputs cause harm, or who can pause or withdraw a
release.

**Recommended response:** Assign named accountable roles for provider/product,
deployment, privacy/security, evaluation, and cultural/community review; maintain an
AI-system record and use-case risk assessment for each materially different deployment;
record approvals, changes, incidents, and residual-risk acceptance.

### G-02 — Cultural and translation provenance is incomplete or not consistently gated

**Severity: High | Evidence status: Partially evidenced**

[`docs/data_governance.md`](../Ethiviz_V8/docs/data_governance.md) defines consent and
review expectations. Prototype metadata in the Buddhist, Hindu, and Indigenous bundles
marks `reviewed: []` and lists machine-generated languages. The Indigenous prototype
comments further acknowledge that the currently supported languages are not Indigenous
languages and that community partnership is needed. The review did not find equivalent
provenance metadata consistently declared across all seven prototype bundles.

[`PrototypeStore.validate_bundle`](../Ethiviz_V8/ethiviz/embeddings/prototype_store.py)
accepts `require_community_consent=False` by default, and its validator checks consent
presence/status but does not enforce the full required reviewer identity, timestamp,
per-entry review, and community-governance schema described in the documentation. The
analysis pathway surfaces translation review status and warnings, which is a useful
transparency control, but a warning is not the same as a promotion gate.

**Why it matters:** Prototype wording directly influences scores. Machine-generated or
unreviewed content can misrepresent the tradition or language it purports to represent,
particularly for Indigenous and other marginalized communities.

**Recommended response:** Define which bundles and languages are enabled for which
intended uses; validate provenance in CI; make consent/review status visible in results
and exports; require community approval before a bundle is promoted to a use that implies
community validity; provide a correction, withdrawal, and dispute process.

### G-03 — Human-reviewed analytical validity is not established

**Severity: High | Evidence status: Not evidenced**

The V8 README explicitly says there is no qualified, consented, human-reviewed evaluation
corpus and that accuracy, calibration, fairness, and cross-cultural validity are not
independently established. The benchmark measures runtime/resource behavior, not
analytical quality. The calibration utility
[`calibration_validation.py`](../Ethiviz_V8/ethiviz/evaluation/calibration_validation.py)
can compute Brier/reliability summaries when labels are supplied, but the repository does
not establish that suitable labels, a reviewed protocol, a held-out evaluation set, or
per-language/per-lens outcome evidence exists. A status emitted by that utility should
not be treated as proof that the product's confidence scores are calibrated.

**Why it matters:** Users may over-rely on plausible numerical scores or confidence
labels even when construct validity, reviewer agreement, and out-of-domain behavior are
unknown.

**Recommended response:** Keep numerical outputs explicitly exploratory; define an
evaluation protocol with qualified reviewers, consent, adjudication, held-out data, and
uncertainty estimates; publish disaggregated findings and limitations before making
performance claims or changing intended use.

### G-04 — Intended-use limitations are documented but not demonstrated as deployment
controls

**Severity: High | Evidence status: Partially evidenced**

The README says not to use inferred demographic attributes for consequential decisions
and excludes default group-fairness/mitigation workflows without suitable labels and
outcomes. The reviewed materials do not establish use-case-specific restrictions,
contractual controls, operator training, or interface/API controls that prevent
downstream use in prohibited workflows. The exact degree of enforcement in a deployment
was not tested.

**Why it matters:** A disclaimer is valuable but may not prevent a deployer or downstream
user from treating scores as an automated decision or a certified fairness result.

**Recommended response:** Define allowed and prohibited uses; put limitations next to
scores in the UI, API schema, and exported reports; require documented human review for
use decisions; provide deployment guidance and terms appropriate to the intended
audience; assess whether additional product-level restrictions are needed.

### G-05 — Privacy and retention guarantees are not fully aligned or verified end to end

**Severity: High | Evidence status: Partially evidenced**

V8 provides request-size, image-count, archive-expansion, quota, queue, and upload-retention
controls, as well as a job deletion endpoint. The V8 README correctly notes that job
deletion alone does not prove erasure from backups or external logs and that Redis and
other retention require deployment review.

However, [`docs/compliance.md`](../Ethiviz_V8/docs/compliance.md) still describes the
"V7 production path" and gives broad statements about a short cleanup window and
conservative defaults without fully reconciling those claims to V8 configuration. The
API upload sweep defaults to 168 hours, and job deletion removes the application job
record, results, related uploads, and audit trail; external queue, database backup,
proxy, and operator-log behavior depends on deployment. No end-to-end retention test
evidence for all these stores was found.

**Why it matters:** Users and operators need accurate retention and deletion statements
for sensitive text, images, and demographic/bias-relevant material. Misstated timelines
can create privacy, contractual, and regulatory exposure.

**Recommended response:** Update the policy to V8 behavior; map data by store, purpose,
retention period, deletion path, and responsible operator; verify application-managed
deletion in supported backends; state backup and external-service limits explicitly;
test and document authorization boundaries.

### G-06 — Job ownership and legacy-record behavior needs explicit migration governance

**Severity: Medium | Evidence status: Evidenced**

In [`api_server.py`](../Ethiviz_V8/Scripts/api_server.py), when authentication is enabled,
`_job_owner_matches` allows access if a job's `owner_key_hash` is absent, as well as when
the owner matches the caller. This preserves access to legacy or unauthenticated-created
jobs. The behavior may be intentional for migration compatibility, but it means every
authenticated key can access an unowned record.

**Why it matters:** A system that transitions from unauthenticated local use to
multi-caller authenticated operation may expose old job data across callers unless
records are migrated, isolated, or purged.

**Recommended response:** Before enabling multi-user authentication on a database with
legacy records, choose and document a migration policy (assign ownership, quarantine,
purge, or keep single-tenant only). Add regression tests for unowned records and make the
deployment mode explicit.

### G-07 — Queue initialization can mask a deployment configuration failure

**Severity: Medium | Evidence status: Evidenced**

[`AnalysisQueue`](../Ethiviz_V8/Scripts/analysis_queue.py) catches exceptions while
connecting to Redis and initializes an in-process `ThreadPoolExecutor` when the RQ queue
is unavailable. This is useful for local development, but if an operator intended a
distributed production queue, startup may continue with different persistence, capacity,
and recovery behavior than expected.

**Why it matters:** Silent mode changes can undermine operational assumptions about
durability, worker separation, and queue capacity.

**Recommended response:** Fail startup when a production configuration explicitly
requires Redis/RQ and Redis is unavailable; otherwise emit a prominent structured
warning and expose the effective queue mode in readiness/diagnostics. Test the failure
path and document development fallback behavior.

### G-08 — Regulatory mapping is not a compliance determination

**Severity: Medium | Evidence status: Partially evidenced**

[`ethiviz/context/regulatory.py`](../Ethiviz_V8/ethiviz/context/regulatory.py) contains a
rule table that maps heuristic findings to named regulatory provisions and recommends
actions. The module includes a disclaimer that its mapping is informational and not legal
advice. The mapping is not evidence that the system or a deployment satisfies, violates,
or is classified under those laws. No legal review of the rule table or jurisdiction-
specific applicability evidence was found.

**Why it matters:** Regulatory references and risk labels can be interpreted as legal
conclusions if surfaced without prominent context.

**Recommended response:** Keep the informational disclaimer at the point of use; label
the mapping as an issue-spotting aid, not a compliance result; require qualified legal
review before use in legal or regulatory workflows; version and date rule content and
document its reviewer.

### G-09 — Accessibility and human-oversight usability are not evidenced by the current
validation setup

**Severity: Medium | Evidence status: Not evidenced**

The V8 CI workflow runs backend and frontend tests and a production build, but the
reviewed workflow does not run an accessibility test suite. No manual assistive-
technology evaluation evidence was found. The repository includes charts and dynamic job
states, so accessibility of equivalent text, keyboard navigation, focus, and status
announcements should be verified rather than assumed.

**Why it matters:** People may be unable to review, interpret, or challenge outputs and
warnings if essential information is only available through inaccessible visual
components or transient state.

**Recommended response:** Test keyboard access and assistive-technology behavior for
submission, progress, errors, result caveats, charts, and exports; add automated
accessibility checks where appropriate and retain manual test evidence.

## 5. Existing controls and positive evidence

The following are evidenced strengths and should be preserved:

- **Purpose and limitations:** V8 describes outputs as exploratory and disclaims
  independent validation, legal determinations, and replacement of human expertise.
- **Network exposure:** API binding validation rejects non-loopback operation without
  API-key configuration and rejects development-debug mode for exposed binding.
- **Authentication and ownership:** API-key validation uses hashed keys and
  timing-safe comparison; owner checks are applied to job access paths, subject to the
  legacy-unowned behavior in G-06.
- **Input/resource controls:** Upload size, image count, XLSX entry count, uncompressed
  size/compression ratio, daily quota, per-key concurrent work, and queue depth are
  bounded in code.
- **Browser and response controls:** V8 documentation describes tab-scoped
  `sessionStorage` for API keys and security headers; tests cover API/security response
  headers and exposed-bind configuration.
- **Audit and deletion mechanisms:** Job-store audit events, audit-chain verification,
  and deletion paths exist, though retention across every deployment store remains
  unresolved.
- **Supply-chain and regression checks:** CI runs backend/frontend tests, frontend
  production build and bundle budget, and a production dependency audit. Dependabot is
  configured at the repository level.
- **Cultural data governance intent:** A written partnership/provenance standard exists,
  and the analysis bridge can surface review state, warnings, and analysis coverage.

These controls reduce risk, but their presence does not establish complete operating
effectiveness or suitability for any specific deployment.

## 6. Assessment summary by governance theme

| Theme | Assessment | Rationale |
|---|---|---|
| Intended purpose and limitations | Partially evidenced | Strong disclaimers exist; deployment-specific use boundaries and enforcement are not established. |
| Accountability and governance | Not evidenced | No current V8 role assignment, risk acceptance, incident, or lifecycle approval evidence reviewed. |
| Risk and impact management | Not evidenced | No deployment-specific AI impact/risk assessment reviewed. |
| Data governance and cultural legitimacy | Partially evidenced | Written standards and some metadata exist; provenance coverage and promotion gates are incomplete. |
| Analytical measurement and validity | Not evidenced | No qualified, consented, human-reviewed validation set or results are established. |
| Transparency and explainability | Partially evidenced | Warnings, coverage, provenance elements, and disclaimers exist; clarity and use effectiveness need validation. |
| Privacy and data lifecycle | Partially evidenced | Several safeguards exist; current policy is stale and full-store retention/deletion is unverified. |
| Security and resilience | Partially evidenced | Auth, bounds, tests, and CI exist; queue fallback and deployment recovery assumptions need control. |
| Human oversight and accessibility | Not evidenced | Human review is recommended, but operational workflow and accessibility evidence are not established. |
| Change and supply-chain management | Partially evidenced | CI and dependency automation exist; AI-specific change review and evidence gates are not established. |

## 7. Recommended release posture

1. Treat the current system as an exploratory prototype, not an independently validated
   evaluator or compliance tool.
2. Do not use its scores as the sole or determinative basis for decisions affecting
   individuals, access to services, employment, education, credit, healthcare, or other
   consequential outcomes.
3. Before any external pilot, name accountable owners, complete a deployment-specific
   risk/impact assessment, reconcile retention policy with implementation, and test
   authentication/ownership and queue-mode assumptions in the target deployment.
4. Do not claim community validation for a language/tradition bundle without appropriate
   consent, qualified review, provenance, and an ongoing correction/withdrawal
   mechanism.
5. Prioritize all High findings and record an accountable owner's acceptance of any
   residual risk before broadening intended use.

See the [Action Register](Action_Register.md) for proposed sequencing and closure
evidence.

## 8. Source references

- [V8 README](../Ethiviz_V8/README.md)
- [Data governance and partnership intake](../Ethiviz_V8/docs/data_governance.md)
- [Compliance and retention documentation](../Ethiviz_V8/docs/compliance.md)
- [PrototypeStore provenance handling](../Ethiviz_V8/ethiviz/embeddings/prototype_store.py)
- [API server authentication, retention, and job handling](../Ethiviz_V8/Scripts/api_server.py)
- [Analysis queue implementation](../Ethiviz_V8/Scripts/analysis_queue.py)
- [Regulatory mapping utility](../Ethiviz_V8/ethiviz/context/regulatory.py)
- [Calibration evaluation utility](../Ethiviz_V8/ethiviz/evaluation/calibration_validation.py)
- [V8 CI workflow](../.github/workflows/ethiviz-v8-ci.yml)
- [V9 improvement proposal](../VERSION_9_IMPROVEMENT_PLAN.md)
- [V9 README and operational limitations](../Ethiviz_V9/README.md)
- [V9 API lifecycle and readiness implementation](../Ethiviz_V9/Scripts/api_server.py)
- [V9 queue implementation](../Ethiviz_V9/Scripts/analysis_queue.py)
- [V9 job-store transitions and retention](../Ethiviz_V9/ethiviz/storage/job_store.py)
- [V9 API benchmark](../Ethiviz_V9/Scripts/benchmark_api.py)
- [V9 plan implementation status](../VERSION_9_IMPROVEMENT_PLAN.md)
