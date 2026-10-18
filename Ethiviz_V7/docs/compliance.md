# EthiViz Data Retention and Regulatory Compliance

This document summarizes how EthiViz handles user data, analysis artifacts, and related governance obligations for the V7 production path.

## Retention policy

- Uploaded input files are retained only as long as required for the active analysis job and a short cleanup window.
- The application deletes uploaded files as part of `DELETE /api/jobs/<job_id>` and also runs a retention sweep for older uploads.
- Persisted job records are kept in SQLite/PostgreSQL and can be purged by authorized callers using `DELETE /api/jobs/<job_id>`.
- The default retention configuration is intentionally conservative and should be tuned to your deployment and legal framework.

## Job deletion and subject access

The operational requirement is simple:

1. A caller with a valid API key may list and inspect only their own jobs.
2. The job owner may delete a job record and any related uploaded files through `DELETE /api/jobs/<job_id>`.
3. An operator can verify the audit log with `GET /api/jobs/<job_id>/audit-log?verify=true`.

This provides a concrete data-subject and operator workflow even before a full enterprise privacy program is in place.

## Regulatory posture

EthiViz maps its findings against the data-governance requirements discussed in `ethiviz/context/regulatory.py` for:

- EU AI Act
- GDPR
- CCPA

The product should be treated as a decision-support tool, not as a fully autonomous decision-maker. The analysis output is useful as a transparency and governance aid, but operators remain responsible for human review.

## Minimum controls

- Keep API keys private and rotate them regularly.
- Log job events and export events to the audit trail.
- Restrict job visibility to the caller's own `owner_key_hash` when auth is enabled.
- Review retention windows against local law and deployment context before longer-term storage is enabled.

## Operational recommendation

For production deployments, pair this policy with a documented deletion schedule, incident-response procedure, and operator responsibilities for any demographic or sensitive inputs processed by the tool.
