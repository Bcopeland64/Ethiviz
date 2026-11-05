#!/usr/bin/env bash
# EthiViz V5 — Stop script.
# Terminal-side counterpart to the in-app "Stop" button (POST /api/stop):
# frees both the backend (5001) and frontend (5173) ports.
# Usage: bash stop_ethiviz.sh

BACKEND_PORT=5001
FRONTEND_PORT=5173

echo "[EthiViz] Stopping backend on port $BACKEND_PORT..."
lsof -ti :$BACKEND_PORT | xargs -r kill 2>/dev/null || true

echo "[EthiViz] Stopping frontend on port $FRONTEND_PORT..."
lsof -ti :$FRONTEND_PORT | xargs -r kill 2>/dev/null || true

echo "[EthiViz] Done."
