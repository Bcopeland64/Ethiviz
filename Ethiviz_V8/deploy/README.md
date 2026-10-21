# Production deployment (Upgrades 42, 46, 48, 49)

`start_ethiviz.sh` runs `python Scripts/api_server.py` directly — Werkzeug's
development server, which the code itself flags as unsuitable for anything
beyond local dev. This directory is the production alternative: gunicorn
behind an nginx TLS-terminating reverse proxy. `start_ethiviz.sh` is
unchanged and remains the dev workflow.

The fastest way to get all of this running together — gunicorn, a Redis
queue, worker processes, Postgres, and the built frontend behind nginx — is
`docker-compose up` from the repository root; see `../docker-compose.yml`
and `../Dockerfile`. This README documents the pieces individually for a
bare-metal/VM deployment, or for understanding what the Compose file wires
together.

## 1. Install gunicorn

```bash
pip install gunicorn
```

## 2. Set required environment variables

At minimum, before running the app anywhere beyond localhost:

```bash
export ETHIVIZ_API_KEYS="<a long random key>,<another key if needed>"
export ETHIVIZ_ALLOWED_ORIGINS="https://your-frontend-domain.example"
export ETHIVIZ_TRUST_PROXY=true   # only once nginx is actually in front of it — see below
```

`ETHIVIZ_API_KEYS` (Upgrade 40) is empty by default, which leaves every route
open with no credential. Do not run this configuration reachable from
anywhere but localhost.

## 3. Run gunicorn

```bash
gunicorn -c deploy/gunicorn_conf.py Scripts.api_server:app
```

See `deploy/gunicorn_conf.py` for worker/thread tuning notes. The shared
`Analyzer` singleton's calibrator/drift-monitor state race (previously
documented as an open issue here) is fixed as of Upgrade 47 — see
`deploy/gunicorn_conf.py`'s comment for how worker count now interacts with
Upgrade 46's optional Redis-backed queue.

## 4. Point nginx at it

Copy `deploy/nginx.conf.sample`, replace `server_name` and the certificate
paths (e.g. from [certbot](https://certbot.eff.org/) — any ACME client
works, this isn't prescriptive) for your own domain, and reload nginx.

## 5. `ETHIVIZ_TRUST_PROXY`

Only set this once nginx (or another reverse proxy) is actually in front of
the app. It makes `request.remote_addr` read the real client IP from
`X-Forwarded-For` instead of the proxy's own connection — without it, every
request behind nginx would appear to come from `127.0.0.1`, which would
silently defeat `/api/stop`'s loopback-only check for anyone going through
the public proxy. Conversely, never set this if the app is reachable
directly (not just through the proxy) — a direct caller could then spoof
`X-Forwarded-For: 127.0.0.1` to impersonate localhost themselves.

## 6. Optional: Redis-backed queue and worker processes (Upgrade 46)

Without `ETHIVIZ_REDIS_URL`, analysis jobs run on an in-process
`ThreadPoolExecutor` (`Scripts/analysis_queue.py`) — fine for a single
gunicorn worker, but request-handling and analysis work then compete for the
same process's threads, and a restart drops any job mid-flight. Setting
`ETHIVIZ_REDIS_URL` (e.g. `redis://127.0.0.1:6379/0`) moves analysis work
onto RQ, run by one or more separate `python Scripts/worker.py` processes,
with one automatic retry on a crashed job:

```bash
export ETHIVIZ_REDIS_URL="redis://127.0.0.1:6379/0"
python Scripts/worker.py            # run one or more of these
```

`ETHIVIZ_QUEUE_MAX_DEPTH` (default 100) bounds how many jobs can be queued
before `/api/analyze` returns 503; `ETHIVIZ_JOB_TIMEOUT` (default 3600
seconds) bounds how long a single RQ job may run.

## 7. Optional: Postgres instead of SQLite (Upgrade 48)

SQLite (the zero-config default) is a single file — fine for one API
process, but the API and `Scripts/worker.py` processes above would each
need to share that same file, which doesn't work across separate hosts.
Setting `DATABASE_URL` to a `postgresql+psycopg://` URL switches
`JobStore` to a Postgres-backed implementation instead, so every process
shares one database:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@db-host:5432/ethiviz"
```

Requires the `postgres` extra: `pip install -e ".[postgres]"`. Leaving
`DATABASE_URL` unset (the default) keeps the original SQLite behavior
unchanged.
