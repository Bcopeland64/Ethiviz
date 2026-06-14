#!/usr/bin/env bash
# EthiViz V5 — Full Platform Start Script
# Starts the Flask API backend and the React frontend together.
# Usage: bash start_ethiviz.sh [--backend-only] [--frontend-only]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
BACKEND_LOG="$SCRIPT_DIR/backend.log"
BACKEND_PORT=5001
FRONTEND_PORT=5173

BACKEND_ONLY=false
FRONTEND_ONLY=false
for arg in "$@"; do
  case $arg in
    --backend-only)  BACKEND_ONLY=true ;;
    --frontend-only) FRONTEND_ONLY=true ;;
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

# ── Activate virtual environment ─────────────────────────────────────────────

if [ -f "$VENV/bin/activate" ]; then
  source "$VENV/bin/activate"
  echo "[EthiViz] Virtual environment activated: $VENV"
else
  echo "[EthiViz] WARNING: No venv found at $VENV"
  echo "          Creating one now..."
  python3 -m venv "$VENV"
  source "$VENV/bin/activate"
fi

# ── Install/verify Python package ────────────────────────────────────────────

if ! python3 -c "import ethiviz" 2>/dev/null; then
  echo "[EthiViz] Installing ethiviz package (editable)..."
  pip install -e "$SCRIPT_DIR/Ethiviz_V4" --quiet
fi

# ── Backend ──────────────────────────────────────────────────────────────────

start_backend() {
  echo "[EthiViz] Starting Flask API backend on port $BACKEND_PORT..."
  check_port "$BACKEND_PORT"

  cd "$SCRIPT_DIR"
  nohup python3 Scripts/api_server.py > "$BACKEND_LOG" 2>&1 &
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
  if [ ! -d "$frontend_dir" ] || [ ! -f "$frontend_dir/package.json" ]; then
    frontend_dir="$SCRIPT_DIR/Ethiviz_V4/project"
  fi

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
