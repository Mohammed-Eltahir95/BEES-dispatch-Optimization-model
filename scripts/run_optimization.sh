#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

CONFIG_PATH="${1:-config/config.yaml}"

echo "Running BESS optimization with config: $CONFIG_PATH"
python -m bess_opt.main --config "$CONFIG_PATH"
