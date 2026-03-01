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

## PQC container (opt-in)

Use the PQC container for opt-in runs that include **liboqs** (ML-KEM, Classic McEliece, etc.).

Prerequisites:
- Docker
- `jq` (Fedora: `sudo dnf install jq`)

Build the PQC image:

```bash
docker build -f docker/Dockerfile.pqc -t pqc-lab:pqc .
```

Notes:

- The PQC container image is immutable.
- These commands assume bash (process substitution `<(...)`).

### Reproducibility check (ML-KEM / liboqs)

Run the ML-KEM profile twice inside the PQC container, save JSON outputs to a mounted `reports/` volume, and compare normalized results with `elapsed_ms` removed.

```bash
mkdir -p reports

docker run --rm \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','profiles/real_mlkem.yaml','--out','/app/reports/run1.json']))"

docker run --rm \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','profiles/real_mlkem.yaml','--out','/app/reports/run2.json']))"

diff -u \
  <(jq 'del(.elapsed_ms)' reports/run1.json) \
  <(jq 'del(.elapsed_ms)' reports/run2.json) \
  || true

jq 'del(.elapsed_ms)' reports/run1.json > /tmp/r1.json
jq 'del(.elapsed_ms)' reports/run2.json > /tmp/r2.json
sha256sum /tmp/r1.json /tmp/r2.json
```

Expected result: diff prints nothing and the two SHA256 hashes match.

### Reproducibility check (Classic McEliece / liboqs)

Run the Classic McEliece profile twice inside the PQC container, save JSON outputs to a mounted `reports/` volume, and compare normalized results with `elapsed_ms` removed. To use a host-side profile, mount `profiles/` read-only into `/app/profiles`. This uses the same `pqc-lab:pqc` image as the ML-KEM run.

Profile: `profiles/real_mceliece.yaml`

```bash
mkdir -p reports

docker run --rm \
  -v "$PWD/profiles:/app/profiles:ro" \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','/app/profiles/real_mceliece.yaml','--out','/app/reports/mceliece_run1.json']))"

docker run --rm \
  -v "$PWD/profiles:/app/profiles:ro" \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','/app/profiles/real_mceliece.yaml','--out','/app/reports/mceliece_run2.json']))"

diff -u \
  <(jq 'del(.elapsed_ms)' reports/mceliece_run1.json) \
  <(jq 'del(.elapsed_ms)' reports/mceliece_run2.json) \
  || true

jq 'del(.elapsed_ms)' reports/mceliece_run1.json > /tmp/m1.json
jq 'del(.elapsed_ms)' reports/mceliece_run2.json > /tmp/m2.json
sha256sum /tmp/m1.json /tmp/m2.json
```

Expected result: diff prints nothing and the two SHA256 hashes match.

### Reproducibility check (Hybrid / liboqs)

Run each hybrid profile twice inside the PQC container, save JSON outputs to a mounted `reports/` volume, and compare normalized results with `elapsed_ms` removed.

Profiles:
- `profiles/real_hybrid_mlkem_frodo.yaml`
- `profiles/real_hybrid_mlkem_hqc.yaml`

```bash
mkdir -p reports

docker run --rm \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','profiles/real_hybrid_mlkem_frodo.yaml','--out','/app/reports/hybrid_frodo_run1.json']))"

docker run --rm \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','profiles/real_hybrid_mlkem_frodo.yaml','--out','/app/reports/hybrid_frodo_run2.json']))"

diff -u \
  <(jq 'del(.elapsed_ms)' reports/hybrid_frodo_run1.json) \
  <(jq 'del(.elapsed_ms)' reports/hybrid_frodo_run2.json) \
  || true

jq 'del(.elapsed_ms)' reports/hybrid_frodo_run1.json > /tmp/hf1.json
jq 'del(.elapsed_ms)' reports/hybrid_frodo_run2.json > /tmp/hf2.json
sha256sum /tmp/hf1.json /tmp/hf2.json

docker run --rm \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','profiles/real_hybrid_mlkem_hqc.yaml','--out','/app/reports/hybrid_hqc_run1.json']))"

docker run --rm \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','profiles/real_hybrid_mlkem_hqc.yaml','--out','/app/reports/hybrid_hqc_run2.json']))"

diff -u \
  <(jq 'del(.elapsed_ms)' reports/hybrid_hqc_run1.json) \
  <(jq 'del(.elapsed_ms)' reports/hybrid_hqc_run2.json) \
  || true

jq 'del(.elapsed_ms)' reports/hybrid_hqc_run1.json > /tmp/hh1.json
jq 'del(.elapsed_ms)' reports/hybrid_hqc_run2.json > /tmp/hh2.json
sha256sum /tmp/hh1.json /tmp/hh2.json
```

Expected result: diff prints nothing and the two SHA256 hashes match.

## Capacity benchmarks (audit-ready dataset)

Current capacity datasets:
- `reports/capacity/mlkem768/`
- `reports/capacity/hybrid_frodo/`
- `reports/capacity/hybrid_hqc/`

These datasets represent burst-model handshake capacity tests with a concurrency sweep and repeated runs, reported with throughput plus latency percentiles (`p50/p95/p99/max`) and failure counts for audit-oriented engineering comparison.

### Reproduce the capacity runs

Methodology and run parameters are documented in `docs/capacity_methodology.md`.

```bash
export GIT_COMMIT="$(git rev-parse --short HEAD)"
mkdir -p reports/capacity/mlkem768

docker run --rm \
  -e GIT_COMMIT="$GIT_COMMIT" \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -m src.capacity.harness \
    --profile profiles/real_mlkem.yaml \
    --concurrency 8 \
    --duration 60 \
    --warmup 10 \
    --out /app/reports/capacity/mlkem768/mlkem768_c8_r1.json
```

Results are host-specific. For cross-run analysis, compare trends (for example knee point and tail-latency behavior) rather than absolute values.

## Capacity Benchmark Campaigns

This repository includes audit-ready PQC capacity benchmark campaigns.

Latest campaign:

- Ryzen 9950X baseline (2026-02-28)
  `docs/capacity/2026-02-28_ryzen9950x_baseline/executive_summary.md`
  `docs/capacity/2026-02-28_ryzen9950x_baseline/report.md`

Campaign datasets include repeatability runs, tail-latency analysis, and CPU saturation measurements for engineering comparison and review.

## Citing

If you use this software or the benchmark datasets, cite the metadata in `CITATION.cff` and reference the release tag `v0.1.0-capacity-baseline-2026-02`.

## License

This project is licensed under the Apache License 2.0. See `LICENSE`.
