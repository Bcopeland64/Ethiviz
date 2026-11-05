# gunicorn -c deploy/gunicorn_conf.py Scripts.api_server:app
#
# start_ethiviz.sh (`python Scripts/api_server.py`) runs Werkzeug's
# development server, which the code itself warns is not meant for anything
# beyond local dev — see the debug/reloader comments at the bottom of
# Scripts/api_server.py. This is the production entry point instead
# (Upgrade 42). It does not replace start_ethiviz.sh; that script is
# unchanged and remains the dev workflow.

import multiprocessing
import os

bind = f"{os.environ.get('ETHIVIZ_HOST', '127.0.0.1')}:{os.environ.get('ETHIVIZ_PORT', '5001')}"

# The Analyzer singleton (bridge.get_analyzer()) lazily loads a ~120MB
# sentence-transformer model and holds mutable calibrator/drift-monitor
# state, shared by every job thread within one process. Upgrade 47 put a
# lock around every mutation, so this is now safe regardless of worker
# count — each gunicorn worker process gets its own independent Analyzer
# singleton (processes don't share memory), and threads within one worker
# no longer race on it. If ETHIVIZ_REDIS_URL is set (Upgrade 46), analysis
# work runs in separate `python Scripts/worker.py` processes instead of
# these gunicorn workers' own threads — scale worker count there for
# analysis throughput, and keep this count sized for request-handling
# capacity (routing, status polling, results/export), not analysis load.
workers = int(os.environ.get('ETHIVIZ_GUNICORN_WORKERS', '2'))
threads = int(os.environ.get('ETHIVIZ_GUNICORN_THREADS', '4'))
worker_class = "gthread"

# Analysis jobs run in a background thread and the request returns
# immediately (202 Accepted) — but model warm-up and large uploads can still
# take a while, so keep the request timeout generous.
timeout = int(os.environ.get('ETHIVIZ_GUNICORN_TIMEOUT', '120'))

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get('ETHIVIZ_LOG_LEVEL', 'info')
