#!/usr/bin/env bash
#
# Claim 5 (paper claim 2): the Bloom filters matter.
# See claim.txt. Prerequisites: ../../install.sh has been run and the evaluation data
# is in ../../data (python3 artifact/download_data.py).
#
# Usage: ./run.sh [-j N] [--data-dir DIR] [--no-run]
#   -j N        worker processes for the figure regeneration (default: all CPUs)
#   --no-run    only re-check figures already regenerated into results/
#
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
# Use the environment created by install.sh, if there is one.
if [ -z "${VIRTUAL_ENV:-}" ] && [ -f "$REPO/.venv/bin/activate" ]; then . "$REPO/.venv/bin/activate"; fi
exec python3 "$REPO/artifact/plots/verify_claims.py" 5 "$@"
