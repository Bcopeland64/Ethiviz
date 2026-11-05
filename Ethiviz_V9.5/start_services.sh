#!/bin/bash
# EthiViz V5 — Quick service launcher (no venv management).
# Assumes dependencies are already installed.
# For full setup with venv, use: bash start_ethiviz.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# See start_ethiviz.sh for why python3.13 rather than a venv/plain python3.
if command -v python3.13 &>/dev/null; then
  PYTHON=python3.13
else
  PYTHON=python3
fi

echo "[EthiViz] Starting backend service (Flask API on port 5001)..."
if [ ! -f "$SCRIPT_DIR/Scripts/api_server.py" ]; then
  echo "Error: Scripts/api_server.py not found!"
  exit 1
fi
$PYTHON "$SCRIPT_DIR/Scripts/api_server.py" > "$SCRIPT_DIR/backend.log" 2>&1 &
BACK_PID=$!
echo "[EthiViz] Backend started (PID $BACK_PID) — http://localhost:5001"

# Give the backend a moment to start
sleep 3

echo "[EthiViz] Starting frontend service (React on port 5173)..."
FRONTEND_DIR="$SCRIPT_DIR/project"
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
  echo "Error: React frontend (package.json) not found!"
  kill "$BACK_PID" 2>/dev/null
  exit 1
fi

trap "echo '[EthiViz] Stopping backend...'; kill $BACK_PID 2>/dev/null" INT TERM EXIT

cd "$FRONTEND_DIR"
npm run dev

echo "[EthiViz] Done."
