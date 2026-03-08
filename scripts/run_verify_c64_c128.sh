#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PROFILE_C64="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c64.yaml"
PROFILE_C128="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c128.yaml"
OUT_DIR="$REPO_ROOT/reports/capacity/mldsa_verify"
OUT_C64="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c64.json"
OUT_C128="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c128.json"

export OQS_INSTALL_PATH=/home/rebel/_oqs
if [ -d "$OQS_INSTALL_PATH/lib64" ]; then
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib64:${LD_LIBRARY_PATH:-}"
else
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib:${LD_LIBRARY_PATH:-}"
fi

cd "$REPO_ROOT"
mkdir -p "$OUT_DIR"

echo "OQS_INSTALL_PATH=$OQS_INSTALL_PATH"
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

echo "== ML-DSA verify capacity: c64 =="
python -m capacity.verify_runner --profile "$PROFILE_C64"

echo "== ML-DSA verify capacity: c128 =="
python -m capacity.verify_runner --profile "$PROFILE_C128"

echo "Output reports:"
echo " - $OUT_C64"
echo " - $OUT_C128"

