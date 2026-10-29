# 11. Risk Register

## Risk Register

| ID | Risk Description | Category | Likelihood | Impact | Owner | Trigger | Response Plan | Status |
|---|---|---|---|---|---|---|---|---|
| R-01 | Platform instability in production-like environments | Technical | High | High | Technical Lead | repeated failures or performance degradation | stabilize architecture, isolate defect patterns, enforce environment parity | Active |
| R-02 | Security controls not fully implemented before launch | Security | Medium | High | Security Lead | audit gaps or missing control validation | implement security checklist, perform review, validate access controls | Active |
| R-03 | Quality issues remain unresolved at release gate | Quality | Medium | High | QA Lead | test failures or unresolved critical bug backlog | increase regression coverage, prioritize defect closure, enforce sign-off | Active |
| R-04 | Insufficient monitoring and runbook coverage | Operations | Medium | High | Operations Lead | missing alerting or unclear incident handling | define runbooks, alerting thresholds, and escalation paths | Active |
| R-05 | Scope creep impacts production delivery | Scope | Medium | Medium | Project Manager | late feature requests without approval | enforce change control and priority review | Active |
| R-06 | Stakeholder trust weakens due to unclear communications | Governance | Medium | Medium | Project Manager | inconsistent updates or delayed decisions | maintain reporting cadence and visibility | Active |
| R-07 | Data handling or privacy concerns surface during launch | Compliance | Medium | High | Security Lead / Product Owner | data classification gaps or usage concerns | classify data, restrict use, confirm handling policy | Active |
| R-08 | Release timeline slips due to dependency bottlenecks | Schedule | Medium | High | Project Manager | delayed approvals or dependency failure | track critical path, escalate blockers, adjust sequencing | Active |
| R-09 | User adoption is limited by unclear value proposition or poor UX | Adoption | Medium | Medium | Product Owner | poor feedback or minimal pilot usage | refine onboarding and messaging, validate with stakeholders | Active |
| R-10 | Insufficient support model after go-live | Operational | Medium | Medium | Operations Lead | no named on-call ownership or escalation coverage | assign support roles and finalize hypercare plan | Active |
| R-11 | No governed human-reviewed evidence for accuracy, fairness, or cultural validity | AI governance | High | High | Product Owner / Evaluation Lead | validity claims or consequential use proposed without evidence | block such claims; define consented evaluation protocol and qualified review | Active |
| R-12 | Production capacity and recovery limits are unmeasured | Technical / Operations | Medium | High | Technical Lead / Operations Lead | worker count, queue capacity, or SLO proposed without representative benchmarks | benchmark target topology and run overload/restart tests before publishing limits | Active |
| R-13 | Deletion expectations exceed application control of backups, logs, or Redis | Privacy / Compliance | Medium | High | Privacy Owner / Operations Lead | deletion request or retention promise includes external copies | map each store, assign retention owner, and disclose unverified infrastructure boundaries | Active |

## Risk Review Notes

- This register should be reviewed at minimum weekly.
- Risk owners are responsible for monitoring triggers and escalation actions.
- Changes in risk status must be documented and communicated to governance stakeholders.
- Critical risks requiring acceptance should be formally logged and signed off by the sponsor.
