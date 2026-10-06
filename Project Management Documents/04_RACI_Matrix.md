# 4. RACI Matrix

## Purpose

The RACI matrix defines responsibility, accountability, consultation, and informed status for key project activities. It clarifies who decides, who does the work, who reviews, and who must be kept informed.

## RACI Legend

- R = Responsible (does the work)
- A = Accountable (final decision owner)
- C = Consulted (provides input)
- I = Informed (kept updated)

## RACI Matrix

| Activity / Deliverable | Executive Sponsor | Project Manager | Product Owner | Technical Lead | Security Lead | QA Lead | Operations Lead | Stakeholders |
|---|---|---|---|---|---|---|---|---|
| Project charter and approval | A | R | C | C | I | I | I | I |
| Scope baseline and change control | A | R | C | C | I | I | I | I |
| Requirements definition | C | R | A | C | C | C | I | I |
| Architecture and technical design | I | C | C | A/R | C | I | I | I |
| Security controls and review | I | C | I | C | A/R | I | I | I |
| QA strategy and release validation | I | C | C | C | I | A/R | I | I |
| Deployment and environment readiness | I | C | I | A/R | C | C | R | I |
| Production monitoring and runbooks | I | C | I | C | I | I | A/R | I |
| Risk management and mitigation | A | R | I | C | C | I | I | I |
| Stakeholder communication | C | A/R | C | I | I | I | I | I |
| Benefit realization review | A | R | C | C | I | I | I | C |
| Go/no-go approval | A | R | C | C | C | C | C | I |

## Governance Notes

- The Executive Sponsor retains final political and business accountability.
- The Project Manager is accountable for schedule, communication, and delivery coordination.
- The Product Owner owns prioritization and business requirement clarity.
- The Technical Lead owns engineering execution and architecture integrity.
- The Security Lead owns prioritization and validation of security controls.
- QA Lead owns release acceptance criteria and quality evidence.
- Operations Lead owns monitoring, support, and service continuity.

## Operational Implication

This matrix ensures accountability is not diffuse. Every critical delivery track has a named accountable owner, and all governance decisions are traceable to a formal decision authority.
