#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PROFILE_C1="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c1.yaml"
PROFILE_C8="$REPO_ROOT/profiles/verify_capacity/mldsa_verify_c8.yaml"
OUT_DIR="$REPO_ROOT/reports/capacity/mldsa_verify"

cd "$REPO_ROOT"

echo "Running verify capacity profile: $PROFILE_C1"
pixi run python -m capacity.verify_runner --profile "$PROFILE_C1"

echo "Running verify capacity profile: $PROFILE_C8"
pixi run python -m capacity.verify_runner --profile "$PROFILE_C8"

echo "Output reports:"
echo " - $OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c1.json"
echo " - $OUT_DIR/mldsa_verify_capacity_real_mldsa_ml-dsa_c8.json"

