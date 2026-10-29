# EthiViz AI Governance Action Register

This register turns the findings in the
[assessment report](AI_Governance_Assessment.md) into proposed work. Priorities are
assessment recommendations, not commitments or findings of legal non-compliance.
Assign an accountable person and target date before treating any action as accepted.

| ID | Priority | Proposed action | Suggested accountable role | Closure evidence |
|---|---|---|---|---|
| A-01 | P0 / High | Establish a V9 AI-system record and deployment-specific intended-use/risk-impact assessment. Identify provider, deployer/operator, affected stakeholders, data categories, foreseeable misuse, human oversight, escalation, and residual-risk approver. | Product/system owner with risk and privacy leads | Approved system record and signed risk/impact assessment, reviewed for each materially different deployment. |
| A-02 | P0 / High | Inventory prototype bundles, source and translated content, reviewer status, consent terms, limitations, and permitted use. Require complete provenance validation in CI and define a community-led promotion, correction, and withdrawal process. | Data steward with community partnership lead | Machine-readable inventory; tests reject incomplete provenance for promoted bundles; review/consent records and documented remediation of draft-only bundles. |
| A-03 | P0 / High | Define a human-reviewed evaluation protocol and establish governed evaluation evidence before making accuracy, calibration, fairness, or cultural-validity claims. | Evaluation lead with qualified reviewers and community partners | Approved protocol; consent and reviewer/adjudication records; held-out results with uncertainty and breakdown by language/lens/domain; release decision record. |
| A-04 | P0 / High | Reconcile V9 privacy and retention documentation with code and each supported deployment. Map upload, job, result, audit, queue, logs, exports, backups, and external services; define periods, deletion behavior, and exceptions. | Privacy/data-protection owner with operations | Current data-flow and retention schedule; tests covering application-managed stores; operator runbook; documented external backup/Redis limits. |
| A-05 | P0 / High | Make intended-use restrictions operational and consistent across UI, API, exports, deployment guidance, and user terms. Define what use is prohibited and require human review for permitted use of outputs. | Product owner with legal/risk reviewer | Approved use policy; user-facing caveats beside results and in exports; representative tests proving caveats persist in all output paths. |
| A-06 | P1 / Medium | Decide and test the policy for unowned legacy jobs before enabling multi-caller authentication. Migrate ownership, quarantine, delete, or keep the deployment single-tenant until resolved. | API/data owner | Migration procedure and tests showing one caller cannot access another caller's legacy job; operator confirmation before auth rollout. |
| A-07 | P1 / Medium | Keep configured Redis/RQ production mode from falling back to the local executor; verify effective mode and fail readiness when the required queue or worker is unavailable. | Platform/operations owner | Startup/configuration tests, readiness behavior, and runbook demonstrating correct failure reporting and recovery. |
| A-08 | P1 / Medium | Review the regulatory-mapping rule table with qualified counsel for the intended markets and make its informational, non-determinative status clear at every user-facing point. | Legal/compliance owner | Versioned legal review, documented applicability limits, reviewer/date metadata, and UI/API language review. |
| A-09 | P1 / Medium | Verify accessibility and human-oversight usability for the end-to-end analysis and export workflow. | Frontend owner with accessibility reviewer | Automated checks in CI plus recorded keyboard and assistive-technology checks for progress, errors, results, warnings, charts, and exports. |
| A-10 | P1 / Medium | Define operational monitoring and incident management for harmful or materially incorrect outputs, privacy events, service failures, and problematic cultural content. Include user reporting, triage, pause/rollback, correction, and notification pathways. | Service owner with support/security leads | Incident playbook, named escalation contacts, tabletop exercise, and a documented issue/correction process available to users. |
| A-11 | P2 / Medium | Establish AI-specific change control for models, prototypes, thresholds, prompts/rules, dependencies, and UI claims. Require risk review and evaluation evidence proportional to the change. | Release manager with evaluation and data owners | Change checklist, versioned artifacts, before/after reports where applicable, approval records, and rollback procedure. |
| A-12 | P2 / Low | Preserve and expand existing security, resource-bound, and dependency checks; add tests for deployment configuration, queue recovery, retention, and claim-preserving exports as the associated work lands. | Engineering and CI owners | CI results linked to release and tests for each changed control; documented exceptions with expiry and owner. |

## Suggested sequencing

1. Complete A-01 and A-04 to establish accountable use context and truthful data
   handling.
2. Complete A-02 and A-03 before making culturally or statistically validity claims.
3. Complete A-05 through A-10 before a broad external pilot or multi-user deployment.
4. Integrate A-11 and A-12 into normal release management.

## Status convention

All actions are **Proposed / Not assessed as complete** at creation. Update status only
when closure evidence is attached and reviewed by the accountable owner. Do not mark an
action complete solely because a document or test exists if the operational control has
not been exercised.

## V9 repository implementation status — 2026-10-29

The statuses below reflect code/document evidence in the V9 snapshot only; they are not
formal closure approvals or evidence from a live deployment.

| Action | V9 status | Evidence / remaining work |
|---|---|---|
| A-01 | Open | No accountable deployment roles, system record, or approved deployment-specific impact assessment was added. |
| A-02 | Open | V9 retains the provenance requirements; community consent and complete provenance validation remain outstanding. |
| A-03 | Open | No consented, qualified, human-reviewed evaluation corpus or held-out validity results were added. |
| A-04 | Partially implemented | V9 documents 168-hour upload and 720-hour terminal-job defaults and removes application-managed job/results/uploads; backups, proxy/log/Redis retention, ownership review, and live deployment expiry remain unverified. |
| A-05 | Partially implemented | The UI and docs retain exploratory-use caveats; intended-use policy, human oversight workflow, and consistency across every output path need review. |
| A-06 | Open | Legacy unowned job behavior is unchanged and still requires an explicit deployment decision. |
| A-07 | Implemented in code; operational proof open | Configured Redis failure now fails startup; readiness checks database, queue, and worker availability. Live outage/recovery tests and operator evidence remain outstanding. |
| A-08 | Open | No qualified legal review of regulatory mapping was added. |
| A-09 | Partially implemented | Progress/cancellation announcements and a cancellation control were added; full keyboard, screen-reader, chart-alternative, and CI accessibility evidence remains outstanding. |
| A-10 | Open | No incident/reporting and response process was added. |
| A-11 | Open | AI-specific change approval and release records remain to be established. |
| A-12 | Partially implemented | V9 adds lifecycle, idempotency, cancellation, readiness, and retention tests and CI; the complete backend suite passed (259 passed, 7 skipped). Production outage/recovery tests and claim-preserving export review remain outstanding. |
