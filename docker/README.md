# Docker CPU Baseline

Build:
  docker build -f docker/Dockerfile.cpu -t pqc-lab:cpu .

Run (default demo):
  docker run --rm pqc-lab:cpu

Run tests:
  docker run --rm pqc-lab:cpu pixi run test

Run demos:
  docker run --rm pqc-lab:cpu pixi run demo-quantum
  docker run --rm pqc-lab:cpu pixi run demo-finance
  docker run --rm pqc-lab:cpu pixi run demo-energy
  docker run --rm pqc-lab:cpu pixi run demo-pqc
