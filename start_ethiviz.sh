#!/usr/bin/env bash
# EthiViz — root convenience wrapper.
# The current project snapshot lives in Ethiviz_V7/ (see Ethiviz_V7/README.md).
# This wrapper exists so `bash
# start_ethiviz.sh` from the repo root keeps working without needing to `cd`.
# Ethiviz_V4/, the root project/, and Scripts/api_server.py are preserved as
# historical snapshots and are no longer executed by this script.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/Ethiviz_V7/start_ethiviz.sh" "$@"
