#!/usr/bin/env bash
set -euo pipefail

RUNTIME="${1:-docker}"
IMAGE="pqc-lab:cpu"
DOCKERFILE="docker/Dockerfile.cpu"

if ! command -v "$RUNTIME" >/dev/null 2>&1; then
  echo "Runtime '$RUNTIME' not found. Use: docker or podman"
  exit 1
fi

echo "== Building image with $RUNTIME =="
"$RUNTIME" build -f "$DOCKERFILE" -t "$IMAGE" .

echo "== Running tests in container =="
"$RUNTIME" run --rm "$IMAGE" pixi run test

echo "== Running default demo in container =="
"$RUNTIME" run --rm "$IMAGE"
