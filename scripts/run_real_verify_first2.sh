#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
POOL_DIR="$REPO_ROOT/fixtures/signatures"
POOL_PATH="$POOL_DIR/mldsa_verify_pool_10000.jsonl"
PROFILE_C1="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c1.yaml"
PROFILE_C8="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c8.yaml"
OUT_DIR="$REPO_ROOT/reports/capacity/mldsa_verify"
OUT_C1="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c1.json"
OUT_C8="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c8.json"

export OQS_INSTALL_PATH=/home/rebel/_oqs
if [ -d "$OQS_INSTALL_PATH/lib64" ]; then
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib64:${LD_LIBRARY_PATH:-}"
else
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib:${LD_LIBRARY_PATH:-}"
fi

cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p "$POOL_DIR" "$OUT_DIR"

echo "OQS_INSTALL_PATH=$OQS_INSTALL_PATH"
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

bash "$REPO_ROOT/scripts/preflight_real_mldsa.sh"

if [ ! -f "$POOL_PATH" ]; then
  echo "Generating verify pool: $POOL_PATH"
  python -m capacity.signature_pool generate \
    --provider real_mldsa \
    --algorithm ML-DSA \
    --pool-size 10000 \
    --out "$POOL_PATH"
else
  echo "Using existing verify pool: $POOL_PATH"
fi

echo "Running verify profile: $PROFILE_C1"
python -m capacity.verify_runner --profile "$PROFILE_C1"

echo "Running verify profile: $PROFILE_C8"
python -m capacity.verify_runner --profile "$PROFILE_C8"

if [ ! -f "$OUT_C1" ]; then
  echo "ERROR: expected output report was not created: $OUT_C1" >&2
  exit 1
fi

if [ ! -f "$OUT_C8" ]; then
  echo "ERROR: expected output report was not created: $OUT_C8" >&2
  exit 1
fi

echo "Output reports:"
echo " - $OUT_C1"
echo " - $OUT_C8"
