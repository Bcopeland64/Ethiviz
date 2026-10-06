# 12. Change Management Control Plan

## Purpose

This plan defines how changes to the Ethiviz_V6 production-readiness effort will be reviewed, approved, tracked, and communicated. It ensures the project remains aligned to scope, schedule, and risk while preventing uncontrolled feature expansion.

## Change Control Principles

- all scope changes must be documented
- no change is approved without explicit impact analysis
- schedule, cost, and risk impact must be considered together
- change decisions must be traceable and logged
- production launch decisions must remain protected from non-essential change noise

## Change Request Process

1. Initiation: change request submitted by stakeholder, team member, or PM.
2. Assessment: PM and relevant leads assess scope, schedule, cost, and risk impact.
3. Review: technical, product, and governance leads evaluate feasibility and implications.
4. Decision: sponsor or designated authority approves, rejects, or defers.
5. Implementation: approved changes are added to the work plan with updated baselines.
6. Closure: result and impact are logged and communicated.

## Change Categories

| Category | Examples | Approval Threshold |
|---|---|---|
| Minor | documentation or low-risk workflow improvements | PM + relevant lead |
| Moderate | feature changes with moderate cost or schedule effect | Product Owner + Technical Lead + PM |
| Major | scope expansion, architectural change, release impact | Sponsor + Steering Committee |

## Change Control Log Fields

- change ID
- date requested
- description
- related requirement or issue
- requester
- impact assessment
- decision status
- approver
- implementation date

## Management Controls

- changes are visible in governance reviews
- no emergency changes are accepted without post-implementation review
- all approved changes are reflected in the project baseline and risk register
- release gates will not be bypassed without documented sponsor approval

## Success Criteria

The change process is effective when it prevents uncontrolled drift while allowing necessary improvements to proceed in a structured and accountable manner. This protects both delivery discipline and product quality.
