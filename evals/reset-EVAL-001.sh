#!/usr/bin/env bash
# Discards previous run state, verifies the original failure, never starts an agent.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
exec python3 "$repo/evals/run-eval.py" --check
