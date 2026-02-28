# Crypto-Agility PQC Test Report (PQC Lab)

## 1. Objective
Demonstrate a reproducible, opt-in PQC testing workflow where key-exchange algorithms can be switched via profiles (crypto-agility), while preserving determinism for auditability.

## 2. Environment

### Host (local workstation)
- OS: Fedora (linux-64)
- Kernel: 6.17.12
- glibc: 2.42
- Archspec: zen4 (from Pixi virtual packages)
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
- PQC provider: liboqs (Open Quantum Safe) via python-oqs (`import oqs`)
- JSON tooling: `jq` on host (used for normalization + diff)
- Mode: single-KEM + hybrid (HKDF-SHA256)

## 3. Methodology
- Profiles define algorithm + provider + deterministic seed:
  - `seed_mode: deterministic`
  - `seed: 1`
  - `iterations: 50`
- Runs emit machine-readable JSON reports to a mounted `reports/` volume.
- Determinism is verified by removing timing noise (`elapsed_ms`) and comparing normalized outputs:
  - `diff -u <(jq 'del(.elapsed_ms)' ...) <(jq 'del(.elapsed_ms)' ...)`
  - SHA256 equality of normalized JSON artifacts.
- `elapsed_ms` values below are example timings from the latest sanity runs and are treated as non-deterministic.

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

## 5. Reproducibility Results

### 5.1 Classic McEliece reproducibility proof
Two independent runs produced identical normalized JSON (with `elapsed_ms` removed).
- Normalization: `jq 'del(.elapsed_ms)'`
- Hash proof (normalized outputs):
  - `/tmp/m1.json` SHA256: `5a1b50b1c96639febc3a3f64ee3d1fa1349c73a2604c66add61a13a865910584`
  - `/tmp/m2.json` SHA256: `5a1b50b1c96639febc3a3f64ee3d1fa1349c73a2604c66add61a13a865910584`

This demonstrates byte-level reproducibility for the deterministic run, excluding timing noise.

## 6. Hybrid Scenarios (Operational)

Hybrid mode combines two liboqs KEMs per iteration and derives a single hybrid shared secret using HKDF-SHA256:
- HKDF input: `ss1 || ss2`
- Salt: `pqc-lab-hybrid`
- Info: `crypto-agility-hybrid`
- Output length: 32 bytes (profile-defined)

Hybrid mode is an operational orchestration test, not a security proof.

### 6.1 Hybrid ML-KEM-768 + FrodoKEM-976-SHAKE
- Profile: `profiles/real_hybrid_mlkem_frodo.yaml`
- Report: `reports/hybrid_mlkem_frodo_sanity.json`
- Iterations: 50, deterministic seed=1
- Result: success_count=50, failure_count=0
- component_shared_secret_lengths: { ML-KEM-768: 32, FrodoKEM-976-SHAKE: 24 }
- derived_shared_secret_length: 32
- Timing example (non-deterministic metric): 214.9097870001242 ms

Interpretation: the hybrid run is materially heavier than the single ML-KEM example timing, reflecting the cost of two KEMs plus HKDF.

### 6.2 Hybrid ML-KEM-768 + HQC-256
- Profile: `profiles/real_hybrid_mlkem_hqc.yaml`
- Report: `reports/hybrid_mlkem_hqc_sanity.json`
- Iterations: 50, deterministic seed=1
- Result: success_count=50, failure_count=0
- component_shared_secret_lengths: { ML-KEM-768: 32, HQC-256: 64 }
- derived_shared_secret_length: 32
- Timing example (non-deterministic metric): 1460.7521759999145 ms

Interpretation: hybrid with HQC-256 is substantially heavier than single-KEM baselines and the Frodo hybrid in these runs.

### 6.3 Reproducibility proofs (hashes)
Hybrid runs were normalized by removing `elapsed_ms`, then compared via diff and SHA256.
- ML-KEM-768 + FrodoKEM-976-SHAKE:
  - `/tmp/hf1.json` == `/tmp/hf2.json`
  - SHA256: `d76302722e266ef6eb36a6273c426e0f280ccc551dcfd02d2db83e24fdbb5193`
- ML-KEM-768 + HQC-256:
  - `/tmp/hh1.json` == `/tmp/hh2.json`
  - SHA256: `a9bdb660cbcdd3e5ec6755c1ca5bee6dddd2629360b816ed8184a15772057eb7`

Hybrid run commands (PQC container, reports mounted):

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

## 7. Observations
- All four single-KEM algorithms and both hybrid scenarios execute through the same harness/provider interface (profile-driven).
- Algorithm choice materially affects runtime cost under identical iterations and environment:
  - Single ML-KEM-768 example timing is ~25.52 ms, while hybrid ML-KEM-768 + FrodoKEM-976-SHAKE is ~214.91 ms (example timing).
  - Hybrid ML-KEM-768 + HQC-256 is ~1460.75 ms (example timing), substantially heavier.
- Shared secret length varies across mechanisms (24/32/64 bytes); hybrid derived_shared_secret_length is 32 bytes by design.
- `elapsed_ms` is treated as non-deterministic noise; determinism is proven via JSON normalization.

## 8. Capacity results snapshot (ML-KEM vs Hybrid Frodo vs Hybrid HQC)

Capacity runs in this repository are interpreted as engineering performance snapshots under the burst handshake model with concurrency sweeps and percentile latency reporting.

Qualitative observations:
- ML-KEM: very low tail latency (including P99) at low concurrency, with throughput typically peaking before the highest concurrency tier.
- Hybrid Frodo: lower single-thread throughput than ML-KEM, with comparatively steadier scaling before tail latency growth becomes dominant.
- Hybrid HQC: earlier saturation under concurrency and stronger high-percentile tail-latency amplification at high load.

Where the data lives:
- `reports/capacity/mlkem768/`
- `reports/capacity/hybrid_frodo/`
- `reports/capacity/hybrid_hqc/`
- `reports/capacity/smoke/` (if generated in a local run)

## 9. Limitations
- This work validates orchestration, determinism, and operational behavior.
- It does not claim cryptographic security proofs, side-channel resistance, or adversarial robustness testing.
- Hybrid mode is an operational proof of orchestration, not a security or side-channel proof.

## 10. Conclusion
PQC Lab demonstrates crypto-agility with reproducible, profile-driven algorithm switching using liboqs, and produces audit-friendly deterministic artifacts suitable for integration into a wider PQC testing infrastructure.
