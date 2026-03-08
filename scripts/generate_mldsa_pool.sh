#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
POOL_DIR="$REPO_ROOT/fixtures/signatures"
POOL_PATH="$POOL_DIR/mldsa_verify_pool_10000.jsonl"

mkdir -p "$POOL_DIR"
cd "$REPO_ROOT"

echo "Generating ML-DSA verify pool at: $POOL_PATH"
if ! pixi run python -m capacity.signature_pool generate \
  --provider real_mldsa \
  --algorithm ML-DSA \
  --pool-size 10000 \
  --out "$POOL_PATH"; then
  echo "ERROR: failed to generate ML-DSA pool. Ensure python-oqs with ML-DSA support is installed." >&2
  exit 1
fi

echo "Wrote: $POOL_PATH"

