#!/usr/bin/env bash
# Rebuild clean workspaces from the existing frozen seed/image only.
# Never invokes BugsInPy checkout or accesses reference metadata.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
exec python3 "$repo/evals/run-eval.py" --check
