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
- Timing example (non-deterministic metric): 25.519632999930764 ms
- Metadata: standard "NIST FIPS 203", note "ML-KEM (formerly CRYSTALS-Kyber)"

Sanity run summary (from `reports/run_sanity_mlkem.json`):
- ok=50, fail=0, ss_len=32, deterministic=true

### 4.2 Classic McEliece (NIST PQC finalist)
- Algorithm: Classic-McEliece-460896
- Provider: liboqs
- Iterations: 50
- Deterministic: true (seed=1)
- Result: success_count=50, failure_count=0
- Shared secret length: 32 bytes
- Timing example (non-deterministic metric): 126.8911510005637 ms
- Metadata: standard "NIST PQC finalist", note "Classic McEliece (code-based KEM) via liboqs"

Sanity run summary (from `reports/mceliece_sanity.json`):
- ok=50, fail=0, ss_len=32, deterministic=true

### 4.3 FrodoKEM-976-SHAKE (NIST PQC, unstructured LWE)
- Algorithm: FrodoKEM-976-SHAKE
- Provider: liboqs
- Iterations: 50
- Deterministic: true (seed=1)
- Result: success_count=50, failure_count=0
- Shared secret length: 24 bytes
- Timing example (non-deterministic metric): 39.94825500001298 ms
- Metadata: standard "NIST PQC (lattice, unstructured LWE)", note "FrodoKEM-976-SHAKE via liboqs (conservative baseline vs ML-KEM)"

### 4.4 HQC-256 (NIST PQC, code-based)
- Algorithm: HQC-256
- Provider: liboqs
- Iterations: 50
- Deterministic: true (seed=1)
- Result: success_count=50, failure_count=0
- Shared secret length: 64 bytes
- Timing example (non-deterministic metric): 54.23221000000922 ms
- Metadata: standard "NIST PQC (code-based)", note "HQC-256 via liboqs (practical code-based KEM baseline)"

## 5. Hybrid Scenarios Tested

Hybrid mode combines two liboqs KEMs per iteration and derives a single hybrid shared secret using HKDF-SHA256:
- HKDF input: `ss1 || ss2`
- Salt: `pqc-lab-hybrid`
- Info: `crypto-agility-hybrid`
- Output length: 32 bytes (profile-defined)

Hybrid profiles (operational, not a security proof):
- ML-KEM-768 + FrodoKEM-976-SHAKE
- ML-KEM-768 + HQC-256

How to run (PQC container, reports mounted):

```bash
mkdir -p reports

docker run --rm \
  -v "$PWD/reports:/app/reports" \
  pqc-lab:pqc \
  pixi run python -c "from src.crypto_agility.run import main; raise SystemExit(main(['--profile','profiles/real_hybrid_mlkem_frodo.yaml','--out','/app/reports/hybrid_mlkem_frodo.json']))"
```

## 6. Reproducibility Results

### 5.1 Classic McEliece reproducibility proof
Two independent runs produced identical normalized JSON (with `elapsed_ms` removed).
- Normalization: `jq 'del(.elapsed_ms)'`
- Hash proof (normalized outputs):
  - `/tmp/m1.json` SHA256: `5a1b50b1c96639febc3a3f64ee3d1fa1349c73a2604c66add61a13a865910584`
  - `/tmp/m2.json` SHA256: `5a1b50b1c96639febc3a3f64ee3d1fa1349c73a2604c66add61a13a865910584`

This demonstrates byte-level reproducibility for the deterministic run, excluding timing noise.

## 7. Observations
- All four algorithms execute through the same harness/provider interface (crypto-agility via profile switching).
- Algorithm choice materially affects runtime cost under identical iterations and environment:
  - ML-KEM-768 is fastest and Classic McEliece-460896 is slowest in these examples; FrodoKEM-976-SHAKE and HQC-256 fall between them.
- Shared secret length varies across mechanisms (24/32/64 bytes), which impacts downstream integration and storage expectations.
- `elapsed_ms` is treated as non-deterministic noise; determinism is proven via JSON normalization.

## 8. Limitations
- This work validates orchestration, determinism, and operational behavior.
- It does not claim cryptographic security proofs, side-channel resistance, or adversarial robustness testing.
- Hybrid mode is an operational proof of orchestration, not a security or side-channel proof.

## 9. Conclusion
PQC Lab demonstrates crypto-agility with reproducible, profile-driven algorithm switching using liboqs, and produces audit-friendly deterministic artifacts suitable for integration into a wider PQC testing infrastructure.
