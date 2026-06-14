#!/bin/bash
# EthiViz V5 — Quick service launcher (no venv management).
# Assumes dependencies are already installed.
# For full setup with venv, use: bash start_ethiviz.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[EthiViz] Starting backend service (Flask API on port 5001)..."
if [ ! -f "$SCRIPT_DIR/Scripts/api_server.py" ]; then
  echo "Error: Scripts/api_server.py not found!"
  exit 1
fi
python3 "$SCRIPT_DIR/Scripts/api_server.py" > "$SCRIPT_DIR/backend.log" 2>&1 &
BACK_PID=$!
echo "[EthiViz] Backend started (PID $BACK_PID) — http://localhost:5001"

# Give the backend a moment to start
sleep 3

echo "[EthiViz] Starting frontend service (React on port 5173)..."
FRONTEND_DIR="$SCRIPT_DIR/Ethiviz_V4/project"
if [ ! -d "$FRONTEND_DIR" ] || [ ! -f "$FRONTEND_DIR/package.json" ]; then
  FRONTEND_DIR="$SCRIPT_DIR/project"
fi
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
  echo "Error: React frontend (package.json) not found!"
  kill "$BACK_PID" 2>/dev/null
  exit 1
fi

trap "echo '[EthiViz] Stopping backend...'; kill $BACK_PID 2>/dev/null" INT TERM EXIT

cd "$FRONTEND_DIR"
npm run dev

echo "[EthiViz] Done."
