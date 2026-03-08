#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PROFILE_C12="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c12.yaml"
PROFILE_C24="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c24.yaml"
PROFILE_C10="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c10.yaml"
OUT_DIR="$REPO_ROOT/reports/capacity/mldsa_verify"
OUT_C12="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c12.json"
OUT_C24="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c24.json"
OUT_C10="$OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c10.json"

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

echo "== ML-DSA verify refinement: c12 =="
python -m capacity.verify_runner --profile "$PROFILE_C12"

echo "== ML-DSA verify refinement: c24 =="
python -m capacity.verify_runner --profile "$PROFILE_C24"

# Optional c10 run for extra knee granularity:
# python -m capacity.verify_runner --profile "$PROFILE_C10"

echo "Output reports:"
echo " - $OUT_C12"
echo " - $OUT_C24"
echo " - optional (disabled by default): $OUT_C10"

