# ML-DSA vs SLH-DSA Verify-Capacity Single-Node Comparison — 2026-05-31

This directory contains a curated comparison package for two single-node local host verify-capacity baselines:

- ML-DSA-65
- SLH-DSA / SPHINCS+-SHA2-128f-simple

## Source packages

- `reports/campaigns/2026-05-31_mldsa-verify-single-node/`
- `reports/campaigns/2026-05-31_slhdsa-verify-single-node/`

## Contents

- `report/mldsa_vs_slhdsa_verify_comparison.md` — curated comparison report
- `summaries/*.csv` — comparison tables and key ratios
- `figures/*.png` and `figures/*.svg` — generated comparison figures
- `manifest.json` and `manifest.sha256` — package-level manifest

## Scope note

This comparison uses single-node local host verify-capacity baselines. No separate SERVER/LOADGEN VM topology was used in this phase.

Raw JSON reports, signature pools, logs, local environment snapshots and helper scripts are intentionally excluded from this curated comparison package.

## Key result

ML-DSA-65 delivered substantially higher peak verify throughput than SLH-DSA/SPHINCS+-SHA2-128f-simple in these single-node runs. ML-DSA reached its practical knee earlier, while SLH-DSA scaled to a higher concurrency point before tail latency became the dominant warning signal.
