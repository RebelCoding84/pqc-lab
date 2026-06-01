# ML-DSA vs SLH-DSA Verify-Capacity Single-VM Comparison — 2026-06-01

This directory contains a curated comparison package for two single-node VM verify-capacity baselines:

- ML-DSA-65
- SLH-DSA / SPHINCS+-SHA2-128f-simple

## Source packages

- `reports/campaigns/2026-06-01_mldsa-verify-single-vm/`
- `reports/campaigns/2026-06-01_slhdsa-verify-single-vm/`

## Contents

- `report/mldsa_vs_slhdsa_vm_verify_comparison.md` — curated comparison report
- `summaries/*.csv` — comparison tables and key ratios
- `figures/*.svg` — generated comparison figures
- `manifest.json` and `manifest.sha256` — package-level manifest

## Scope note

This comparison uses single-node VM verify-capacity baselines. No separate SERVER/LOADGEN VM topology was used in this phase.

Raw JSON reports, signature pools, logs, full local environment snapshots and helper scripts are intentionally excluded from this curated comparison package.

## Key result

ML-DSA-65 delivered 3.25x higher peak verify throughput than SLH-DSA/SPHINCS+-SHA2-128f-simple in this single-VM baseline. Both algorithms peaked at c8 in this default scheduler-managed VM configuration.
