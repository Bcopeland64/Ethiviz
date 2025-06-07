#!/bin/bash

set -e

echo "Starting backend service..."
if [ ! -f "Scripts/api_server.py" ]; then
    echo "Error: Backend script Scripts/api_server.py not found!"
    exit 1
fi
python3 Scripts/api_server.py &
sleep 10

echo "Starting frontend service..."
if [ ! -d "project" ] || [ ! -f "project/package.json" ]; then
    echo "Error: Frontend directory 'project' or 'project/package.json' not found!"
    exit 1
fi
cd project
npm run dev

echo "Backend and frontend services initiated. Frontend will run in this terminal. Backend is running in the background."
