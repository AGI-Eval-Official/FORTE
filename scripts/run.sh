#!/usr/bin/env bash
# Minimal benchmark wrapper for FORTE.
#
# Defaults:
#   - model: agents.defaults.model.primary from openclaw_config/openclaw.json
#   - suite: all tasks
#
# Optional overrides:
#   MODEL=provider/model-a bash scripts/run.sh
#   TASK_ID=administration-001 bash scripts/run.sh
#   SUITE=administration-001,Finance-018 bash scripts/run.sh
#   RUNS=3 CONCURRENCY=2 bash scripts/run.sh
set -euo pipefail

MODEL="${MODEL:-}"
TASK_ID="${TASK_ID:-}"
SUITE="${SUITE:-${TASK_ID}}"
DATASET="${DATASET:-./data}"
OUTPUT_DIR="${OUTPUT_DIR:-./results}"
RUNS="${RUNS:-3}"
CONCURRENCY="${CONCURRENCY:-3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

cmd=(
  python scripts/benchmark.py
  --dataset "$DATASET"
  --runs "$RUNS"
  --concurrency "$CONCURRENCY"
  --output-dir "$OUTPUT_DIR"
)

if [[ -n "$MODEL" ]]; then
  cmd+=(--model "$MODEL")
fi

if [[ -n "$SUITE" ]]; then
  cmd+=(--suite "$SUITE")
fi

exec "${cmd[@]}" "$@"
