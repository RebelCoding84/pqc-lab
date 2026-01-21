#!/usr/bin/env bash
set -euo pipefail

echo "== Runtime check =="

if command -v podman >/dev/null 2>&1; then
  echo "[OK] podman: $(podman --version)"
  if podman info >/dev/null 2>&1; then
    echo "[OK] podman info works"
  else
    echo "[WARN] podman installed but 'podman info' failed"
  fi
else
  echo "[INFO] podman not found"
fi

if command -v docker >/dev/null 2>&1; then
  echo "[OK] docker: $(docker --version)"
  if docker info >/dev/null 2>&1; then
    echo "[OK] docker info works"
  else
    echo "[WARN] docker installed but 'docker info' failed (daemon/group?)"
  fi
else
  echo "[INFO] docker not found"
fi

echo "DOCKER_HOST=${DOCKER_HOST:-<empty>}"
