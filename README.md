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

## Crypto-Agility Test Harness

This harness proves orchestration, deterministic execution, and profile-driven algorithm switching for key-exchange mock baselines. It does NOT provide real cryptography or security guarantees; the mock algorithms are strictly non-production scaffolding.

Run the example profiles:

```bash
pixi run python -m crypto_agility.run --profile profiles/mock_ecdh.yaml
pixi run python -m crypto_agility.run --profile profiles/mock_pqc_kem.yaml
```

If you change dependencies (for example adding PyYAML), run `pixi install` to refresh `pixi.lock`.

## Extension Strategy

The baseline is CPU-only and intentionally minimal. Additional capabilities (PQC provider libraries, GPU acceleration, or containerized deployments) can be added later via Pixi profiles without changing the core baseline.
