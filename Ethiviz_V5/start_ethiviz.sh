#!/usr/bin/env bash
# EthiViz V5 — Full Platform Start Script
# Starts the Flask API backend and the React frontend together.
# Usage: bash start_ethiviz.sh [--backend-only] [--frontend-only] [--with-vision]
#
# To stop everything: click the Stop button in the app header, or run
# `bash stop_ethiviz.sh` from another terminal.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_LOG="$SCRIPT_DIR/backend.log"
BACKEND_PORT=5001
FRONTEND_PORT=5173

# Prefer python3.13 (verified to already have core deps — numpy/pandas/flask/
# pydantic/scikit-learn — installed under the user's site-packages) over a
# venv. A venv was tried here previously but was left in a broken state (no
# python3 binary in venv/bin, and its recorded Python version didn't match
# where dependencies actually live) — using the system interpreter directly
# sidesteps that rather than depending on a venv that doesn't work.
if command -v python3.13 &>/dev/null; then
  PYTHON=python3.13
else
  PYTHON=python3
fi

BACKEND_ONLY=false
FRONTEND_ONLY=false
WITH_VISION=false
for arg in "$@"; do
  case $arg in
    --backend-only)  BACKEND_ONLY=true ;;
    --frontend-only) FRONTEND_ONLY=true ;;
    --with-vision)   WITH_VISION=true ;;
  esac
done

# ── Helpers ──────────────────────────────────────────────────────────────────

print_banner() {
  echo ""
  echo "  ╔══════════════════════════════════════════════════╗"
  echo "  ║           EthiViz V5 — Cultural Bias Platform    ║"
  echo "  ╠══════════════════════════════════════════════════╣"
  echo "  ║  7 ethical lenses · AIF360 parity · SQLite jobs  ║"
  echo "  ╚══════════════════════════════════════════════════╝"
  echo ""
}

check_port() {
  local port=$1
  if lsof -ti :"$port" &>/dev/null; then
    echo "[EthiViz] Port $port is in use — stopping existing process..."
    kill "$(lsof -ti :"$port")" 2>/dev/null || true
    sleep 1
  fi
}

echo "[EthiViz] Using interpreter: $($PYTHON --version) ($(command -v $PYTHON))"

# ── Install/verify Python packages ───────────────────────────────────────────

if ! $PYTHON -c "import ethiviz" 2>/dev/null; then
  echo "[EthiViz] Installing ethiviz package (editable)..."
  $PYTHON -m pip install --user -e "$SCRIPT_DIR" --quiet
fi

if ! $PYTHON -c "import flask, flask_cors" 2>/dev/null; then
  echo "[EthiViz] Installing Flask + flask-cors..."
  $PYTHON -m pip install --user flask flask-cors --quiet
fi

# Vision extras (mediapipe/torch/transformers/opencv) are a multi-GB install
# and are NOT installed by default — image analysis degrades gracefully
# without them (see Scripts/ethiviz_bridge.py HAS_VISION). Opt in explicitly.
if $WITH_VISION; then
  if ! $PYTHON -c "import mediapipe, torch, transformers" 2>/dev/null; then
    echo "[EthiViz] Installing vision extras (mediapipe/torch/transformers/opencv)..."
    echo "          This is a large download and may take several minutes."
    $PYTHON -m pip install --user -e "$SCRIPT_DIR[vision]" --quiet
  else
    echo "[EthiViz] Vision extras already installed."
  fi
fi

# ── Backend ──────────────────────────────────────────────────────────────────

start_backend() {
  echo "[EthiViz] Starting Flask API backend on port $BACKEND_PORT..."
  check_port "$BACKEND_PORT"

  cd "$SCRIPT_DIR"
  nohup $PYTHON Scripts/api_server.py > "$BACKEND_LOG" 2>&1 &
  BACK_PID=$!
  echo "[EthiViz] Backend running — PID $BACK_PID — log: $BACKEND_LOG"
  echo "[EthiViz] API: http://localhost:$BACKEND_PORT"
  echo ""
  echo "  Available endpoints:"
  echo "    POST /api/analyze"
  echo "    GET  /api/analyze/status/{job_id}"
  echo "    GET  /api/analyze/results/{job_id}"
  echo "    GET  /api/analyze/results/{job_id}/export?format=html|json"
  echo "    GET  /api/jobs            (persistent history)"
  echo "    POST /api/compare         (dataset comparison)"
  echo "    GET  /api/sample-data     (140+ curated examples)"
  echo "    POST /api/stop            (graceful shutdown — also see stop_ethiviz.sh)"
  echo ""

  # Wait for backend to be ready
  local tries=0
  until curl -s "http://localhost:$BACKEND_PORT/api/sample-data" &>/dev/null || [ $tries -ge 15 ]; do
    sleep 1
    tries=$((tries + 1))
  done
  if [ $tries -ge 15 ]; then
    echo "[EthiViz] WARNING: Backend did not respond within 15s. Check $BACKEND_LOG"
  else
    echo "[EthiViz] Backend ready."
  fi
}

# ── Frontend ─────────────────────────────────────────────────────────────────

start_frontend() {
  local frontend_dir="$SCRIPT_DIR/project"

  if [ ! -f "$frontend_dir/package.json" ]; then
    echo "[EthiViz] WARNING: React frontend not found. Skipping frontend start."
    return
  fi

  # Ensure Node v16+ via nvm (system Node may be too old for Vite)
  if [ -f "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
    nvm use --lts --silent 2>/dev/null || nvm use node --silent 2>/dev/null || true
    echo "[EthiViz] Node version: $(node --version)"
  fi

  echo "[EthiViz] Starting React frontend on port $FRONTEND_PORT..."
  check_port "$FRONTEND_PORT"

  cd "$frontend_dir"
  if [ ! -d "node_modules" ]; then
    echo "[EthiViz] Installing frontend dependencies (npm install)..."
    npm install --silent
  fi

  echo "[EthiViz] UI: http://localhost:$FRONTEND_PORT"
  echo ""
  npm run dev
}

# ── Main ─────────────────────────────────────────────────────────────────────

print_banner

if $BACKEND_ONLY; then
  start_backend
  echo "[EthiViz] Backend-only mode. Tailing log (Ctrl-C to stop)..."
  tail -f "$BACKEND_LOG"
elif $FRONTEND_ONLY; then
  start_frontend
else
  start_backend

  # Trap Ctrl-C to kill backend when frontend exits
  trap 'echo ""; echo "[EthiViz] Stopping backend (PID $BACK_PID)..."; kill $BACK_PID 2>/dev/null; exit 0' INT TERM

  start_frontend

  echo "[EthiViz] Frontend stopped. Stopping backend (PID $BACK_PID)..."
  kill "$BACK_PID" 2>/dev/null || true
fi
