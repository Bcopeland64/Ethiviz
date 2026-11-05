# EthiViz V7 — Upgrade 49 (Containerization). Multi-stage: a Node stage
# builds the React frontend, a Python stage installs third-party
# dependencies, and two final targets are selected via `--target` in
# docker-compose.yml:
#   - `runtime`  — the Flask API (Scripts/api_server.py) and the RQ worker
#                  (Scripts/worker.py) both use this image; which one runs
#                  is chosen by the command in docker-compose.yml, not by
#                  building two separate images for near-identical code.
#   - `frontend` — nginx serving the built React app and reverse-proxying
#                  /api to the `runtime` API service.
#
# Build context is this directory (Ethiviz_V6/) — see docker-compose.yml,
# which lives alongside this file.

ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=20

# ── Frontend build ───────────────────────────────────────────────────────────
FROM node:${NODE_VERSION}-slim AS frontend-builder
WORKDIR /app
COPY project/package.json project/package-lock.json ./
RUN npm ci
COPY project/ ./
# Vite inlines VITE_* env vars into the bundle at build time (not runtime) —
# see ConfigPanel.tsx/CrossCulturalEquityDashboard.tsx's API_BASE_URL.
# docker-compose.yml passes this as a build arg so the compose-built image
# talks to nginx's own origin (deploy/nginx.docker.conf) instead of the
# 'http://localhost:5001' default meant for `npm run dev`.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ── Python dependency install ────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS python-deps
WORKDIR /build
# ETHIVIZ_EXTRAS controls which optional-dependency groups from
# pyproject.toml are installed. `api` (Flask/CORS/rate-limiting/upload
# verification) and `queue` (redis/rq — Scripts/worker.py hard-imports
# these) are required for the app to run in this image at all; `postgres`
# (sqlalchemy/psycopg) is included by default so docker-compose.yml's
# Postgres service works out of the box, but is genuinely optional — SQLite
# remains the code's own zero-config default without DATABASE_URL (Upgrade
# 48). Heavy extras (vision/semantic/multilingual, multi-GB with
# torch/transformers) are deliberately NOT in the default build — pass
# `--build-arg ETHIVIZ_EXTRAS=api,queue,postgres,vision,semantic` to include
# them, mirroring start_ethiviz.sh's opt-in `--with-vision` flag.
ARG ETHIVIZ_EXTRAS=api,queue,postgres
COPY pyproject.toml README.md ./
COPY ethiviz/ ./ethiviz/
RUN pip install --no-cache-dir --prefix=/install gunicorn ".[${ETHIVIZ_EXTRAS}]" && \
    # This install pulls in every third-party dependency correctly, but
    # setuptools' default file discovery only packages *.py — none of
    # ethiviz's *.yaml/*.json data files (framework definitions, prototype
    # translations, calibration data; verified directly: a plain `pip
    # install` of this project installs 0 of the 21 .yaml files under
    # ethiviz/ into site-packages). Rather than add package-data config
    # that both this Docker build and every other install path would need
    # to stay in sync with, the runtime stage below copies the real
    # `ethiviz/` source directory instead and this incomplete installed
    # copy is deleted so there's exactly one, unambiguous copy on sys.path.
    rm -rf /install/lib/python*/site-packages/ethiviz*

# ── Runtime (API + worker) ───────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime
# Non-root user (Upgrade 49) — the app has no reason to run as root, and a
# container escape from a root process is strictly worse than from one that
# already has minimal privileges.
RUN groupadd --gid 1000 ethiviz && \
    useradd --uid 1000 --gid ethiviz --shell /bin/bash --create-home ethiviz
WORKDIR /app
COPY --from=python-deps /install /usr/local
# ethiviz/ is copied as source, not pip-installed — see the comment in the
# python-deps stage above for why. Scripts/api_server.py already appends
# this directory (its own parent) to sys.path at import time, which is what
# makes `import ethiviz...` and `import Scripts...` resolve here without
# either being on PYTHONPATH explicitly.
COPY ethiviz/ ./ethiviz/
COPY Scripts/ ./Scripts/
COPY deploy/gunicorn_conf.py ./deploy/gunicorn_conf.py
COPY pyproject.toml README.md ./
RUN mkdir -p /home/ethiviz/.ethiviz && chown -R ethiviz:ethiviz /home/ethiviz /app
USER ethiviz
ENV ETHIVIZ_ENV=production \
    ETHIVIZ_HOST=0.0.0.0 \
    ETHIVIZ_PORT=5001 \
    PYTHONUNBUFFERED=1
EXPOSE 5001
# gunicorn (deploy/gunicorn_conf.py, Upgrade 42) rather than
# `python Scripts/api_server.py`'s Werkzeug dev server — see deploy/README.md.
# docker-compose.yml overrides `command:` for the worker service to run
# `python Scripts/worker.py` instead, from this same image.
CMD ["gunicorn", "-c", "deploy/gunicorn_conf.py", "Scripts.api_server:app"]

# ── Frontend (nginx) ──────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS frontend
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY deploy/nginx.docker.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
