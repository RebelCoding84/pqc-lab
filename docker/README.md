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

# PQC container

Build:
  docker build -f docker/Dockerfile.pqc -t pqc-lab:pqc .

Build (pin refs):
  docker build -f docker/Dockerfile.pqc -t pqc-lab:pqc \
    --build-arg LIBOQS_REF=0.10.0 \
    --build-arg LIBOQS_PY_REF=0.10.0 .

Run (verify):
  docker run --rm pqc-lab:pqc python3 -c "import oqs; print(oqs.__version__)"
