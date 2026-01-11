# PQC Lab (CPU Baseline)

This repository provides a CPU-only, reproducible baseline environment for an EU-style PQC testing lab. The baseline stays green in CI even when optional PQC providers are not installed.

## Quickstart

1) Install Pixi: https://pixi.sh
2) Install dependencies:

```bash
pixi install
```

3) Run tests:

```bash
pixi run test
```

4) Run demos:

```bash
pixi run demo-quantum
pixi run demo-finance
pixi run demo-energy
pixi run demo-pqc
```

## Extension Strategy

The baseline is CPU-only and intentionally minimal. Additional capabilities (PQC provider libraries, GPU acceleration, or containerized deployments) can be added later via Pixi profiles without changing the core baseline.
