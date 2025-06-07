#!/usr/bin/env bash

# EthiViz Start Script: Starts both Flask backend and React frontend
# Usage: bash start_ethiviz.sh

set -e

# --- Backend ---
echo "[EthiViz] Starting backend (Flask API)..."
if [ ! -d "venv" ]; then
  echo "[EthiViz] Python virtual environment not found. Creating venv..."
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm --quiet
# Start backend in background
nohup python3 Scripts/api_server.py > backend.log 2>&1 &
BACK_PID=$!
echo "[EthiViz] Backend running (PID $BACK_PID, log: backend.log) at http://localhost:5001"

# --- Frontend ---
echo "[EthiViz] Starting frontend (React)..."
cd project
if [ ! -d "node_modules" ]; then
  echo "[EthiViz] Installing frontend dependencies..."
  npm install
fi
npm run dev

# When the frontend server stops, kill the backend
echo "[EthiViz] Stopping backend (PID $BACK_PID)..."
kill $BACK_PID 