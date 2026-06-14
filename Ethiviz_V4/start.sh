#!/usr/bin/env bash
# EthiViz V5 — library server start script
# Starts the Flask API backend only (for library/API usage without the React UI).
# Usage: ./start.sh [port]
set -e

PORT=${1:-5001}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/../venv"

cd "$SCRIPT_DIR"

# Activate venv if present
if [ -f "$VENV/bin/activate" ]; then
  source "$VENV/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  source "$SCRIPT_DIR/venv/bin/activate"
fi

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found." >&2
  exit 1
fi

# Ensure ethiviz is installed
if ! python3 -c "import ethiviz" 2>/dev/null; then
  echo "ethiviz package not found — installing in editable mode..."
  python3 -m pip install -e . --quiet
fi

# Kill anything already on the port and wait until it's free
if lsof -ti :"$PORT" &>/dev/null; then
  echo "Port $PORT in use — stopping existing process..."
  lsof -ti :"$PORT" | xargs -r kill -9 2>/dev/null || true
  for i in $(seq 1 20); do
    lsof -ti :"$PORT" &>/dev/null || break
    sleep 0.5
  done
  if lsof -ti :"$PORT" &>/dev/null; then
    echo "ERROR: port $PORT still in use after 10s — aborting." >&2
    exit 1
  fi
fi

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║         EthiViz V5 — API Server      ║"
echo "  ╠══════════════════════════════════════╣"
echo "  ║  API  : http://localhost:$PORT         ║"
echo "  ║  Logs : /tmp/ethiviz_api.log          ║"
echo "  ║  Stop : Ctrl-C                        ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  Endpoints:"
echo "    POST /api/analyze"
echo "    GET  /api/analyze/status/{job_id}"
echo "    GET  /api/analyze/results/{job_id}"
echo "    GET  /api/analyze/results/{job_id}/export?format=html|json"
echo "    GET  /api/jobs"
echo "    POST /api/compare"
echo "    GET  /api/sample-data"
echo ""

# Run API server — logs to file AND terminal
exec python3 -m ethiviz.server 2>&1 | tee /tmp/ethiviz_api.log
