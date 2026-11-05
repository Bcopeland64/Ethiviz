# EthiViz V9 Data Retention and Regulatory Notes

This document describes V9 application behavior, not a legal determination or guarantee
about a particular deployment. Operators must assess applicable requirements, backups,
reverse proxies, monitoring systems, and external infrastructure separately.

## Application retention defaults

| Data location | Default behavior | Configuration / responsibility |
|---|---|---|
| Uploaded files | Deleted by an hourly sweep after 168 hours; explicit job deletion removes associated uploads immediately. | `ETHIVIZ_UPLOAD_RETENTION_HOURS`; operators control the host filesystem and backups. |
| Terminal job records and stored results | Completed, failed, and cancelled jobs are deleted after 720 hours; pending/running jobs are not swept. An audit event is retained. | `ETHIVIZ_JOB_RETENTION_HOURS`; `0` disables time-based job expiry. |
| SQLite/PostgreSQL audit events | Minimal lifecycle/export metadata remains after job deletion to preserve the hash chain. It may include the job UUID and timestamps. | Operators must define an audit retention period and database backup lifecycle. |
| Queue data | V9 does not configure Redis persistence or retention. | Redis administrators must define persistence, backup, access, and expiry policies. |
| Application/proxy/backup logs | V9 avoids logging input content and upload filenames in its API request/error paths, but cannot govern all infrastructure logs or historical entries. | Operators must configure log access, rotation, retention, and backup expiry. |

These periods are defaults, not a promise of complete erasure. Job deletion and scheduled
expiry remove application-managed result rows and uploads but do not erase copies already
made by a database backup, proxy, client, or external service.

## Job access and lifecycle

- When API-key authentication is enabled, V9 checks job ownership before returning status,
  results, audit events, cancellation, or deletion.
- `DELETE /api/jobs/<job_id>` removes the job record, stored results, uploaded files, and
  idempotency mapping. A minimal deletion event remains in the audit log.
- `GET /api/jobs/<job_id>/audit-log?verify=true` checks the append-only audit hash chain.
- `POST /api/jobs/<job_id>/cancel` only cancels queued jobs. Running work is not safely
  interruptible and returns `409` rather than claiming cancellation.
- `Idempotency-Key` supports safe resubmission. The store keeps key/request digests, not
  the submitted text or raw key.

## Regulatory posture and use limits

`ethiviz/context/regulatory.py` provides informational mappings for the EU AI Act, GDPR,
and CCPA. These mappings are not legal advice or a compliance determination. EthiViz
results are exploratory decision-support signals; a deployer remains responsible for
intended-use controls, qualified human review, affected-person safeguards, and any
required legal assessment.

No human-reviewed evaluation corpus or community authorization is included. Do not treat
prototype translations, scores, or inferred attributes as validated evidence or use them
alone for consequential decisions.
