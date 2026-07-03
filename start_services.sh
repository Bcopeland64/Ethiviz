#!/usr/bin/env bash
# EthiViz — root convenience wrapper. See Ethiviz_V5/start_services.sh (the
# real, maintained copy) and start_ethiviz.sh for context.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/Ethiviz_V5/start_services.sh" "$@"
