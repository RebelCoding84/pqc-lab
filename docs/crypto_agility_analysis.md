# Crypto-Agility PQC Test Report (PQC Lab)

## 1. Objective
Demonstrate a reproducible, opt-in PQC testing workflow where key-exchange algorithms can be switched via profiles (crypto-agility), while preserving determinism for auditability.

## 2. Environment

### Host (local workstation)
- OS: Fedora (linux-64)
- CPU arch hint: zen4 (from Pixi virtual packages)
- Pixi: 0.62.2
- Workspace: `pqc-lab` v0.1.0
- Workspace env (default):
  - Channels: conda-forge
  - Dependencies (10): python, pip, hatchling, qiskit, qiskit-aer, numpy, scipy, pytest, rich, pyyaml

### PQC container (opt-in)
- Image: `pqc-lab:pqc`
- Built from: `docker/Dockerfile.pqc`
- Base image: Ubuntu 24.04
- Python (inside container via Pixi): `3.11.14 | packaged by conda-forge | (main, Oct 22 2025, 22:46:25) [GCC 14.3.0]`
- PQC provider: liboqs (Open Quantum Safe)
- JSON tooling: `jq` on host (used for normalization + diff)

## 3. Methodology
- Profiles define algorithm + provider + deterministic seed:
  - `seed_mode: deterministic`
  - `seed: 1`
  - `iterations: 50`
- Runs emit machine-readable JSON reports to a mounted `reports/` volume.
- Determinism is verified by removing timing noise (`elapsed_ms`) and comparing normalized outputs:
  - `diff -u <(jq 'del(.elapsed_ms)' ...) <(jq 'del(.elapsed_ms)' ...)`
  - SHA256 equality of normalized JSON artifacts.

## 4. Algorithms Tested

### 4.1 ML-KEM (NIST FIPS 203)
- Algorithm: ML-KEM-768
- Provider: liboqs
- Iterations: 50
- Deterministic: true (seed=1)
- Result: success_count=50, failure_count=0
- Shared secret length: 32 bytes
- Timing example (non-deterministic metric): 25.5196 ms

Sanity run summary (from `reports/run_sanity_mlkem.json`):
- ok=50, fail=0, ss_len=32, deterministic=true

### 4.2 Classic McEliece (NIST PQC finalist)
- Algorithm: Classic-McEliece-460896
- Provider: liboqs
- Iterations: 50
- Deterministic: true (seed=1)
- Result: success_count=50, failure_count=0
- Shared secret length: 32 bytes
- Timing example (non-deterministic metric): 126.8912 ms

Sanity run summary (from `reports/mceliece_sanity.json`):
- ok=50, fail=0, ss_len=32, deterministic=true

## 5. Reproducibility Results

### 5.1 Classic McEliece reproducibility proof
Two independent runs produced identical normalized JSON (with `elapsed_ms` removed).
- Normalization: `jq 'del(.elapsed_ms)'`
- Hash proof (normalized outputs):
  - `/tmp/m1.json` SHA256: `5a1b50b1c96639febc3a3f64ee3d1fa1349c73a2604c66add61a13a865910584`
  - `/tmp/m2.json` SHA256: `5a1b50b1c96639febc3a3f64ee3d1fa1349c73a2604c66add61a13a865910584`

This demonstrates byte-level reproducibility for the deterministic run, excluding timing noise.

## 6. Observations
- Both algorithms execute through the same harness/provider interface (crypto-agility via profile switching).
- Algorithm choice materially affects runtime cost under identical iterations and environment:
  - ML-KEM-768 is faster than Classic McEliece-460896 in this setup (timing varies, but consistently higher for McEliece in these runs).

## 7. Limitations
- This work validates orchestration, determinism, and operational behavior.
- It does not claim cryptographic security proofs, side-channel resistance, or adversarial robustness testing.

## 8. Conclusion
PQC Lab demonstrates crypto-agility with reproducible, profile-driven algorithm switching using liboqs, and produces audit-friendly deterministic artifacts suitable for integration into a wider PQC testing infrastructure.
