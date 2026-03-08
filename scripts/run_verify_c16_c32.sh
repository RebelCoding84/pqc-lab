#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PROFILE_C16="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c16.yaml"
PROFILE_C32="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c32.yaml"
OUT_DIR="$REPO_ROOT/reports/capacity/mldsa_verify"
OUT_C16="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c16.json"
OUT_C32="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c32.json"

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

echo "== ML-DSA verify capacity: c16 =="
python -m capacity.verify_runner --profile "$PROFILE_C16"

echo "== ML-DSA verify capacity: c32 =="
python -m capacity.verify_runner --profile "$PROFILE_C32"

echo "Output reports:"
echo " - $OUT_C16"
echo " - $OUT_C32"
