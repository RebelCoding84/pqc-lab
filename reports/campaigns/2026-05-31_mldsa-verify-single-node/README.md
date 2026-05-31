# ML-DSA Verify-Capacity Single-Node Baseline — 2026-05-31

This directory contains a curated publication package for a single-node ML-DSA verify-capacity baseline.

## Included profile

- ML-DSA-65 verify-capacity
- Provider: `real_mldsa`
- Operation: `verify`
- Pool size: 10,000 pre-generated signatures
- Warmup: 3 seconds
- Duration: 20 seconds
- Repeats: 3

## Measured concurrency points

- c1
- c8
- c10
- c12
- c16
- c24
- c32

## Contents

- `report/mldsa_verify_report.md` — curated Markdown report
- `summaries/mldsa_verify_summary.csv` — summary table for all measured points
- `figures/*.png` and `figures/*.svg` — generated figures
- `manifest.json` and `manifest.sha256` — package-level manifest

## Scope note

This is a single-node verify-capacity baseline. Signing work is excluded from the measurement loop by using a pre-generated signature pool.

At high-throughput points, latency sampling may hit the runner cap. Throughput is based on total operation counts, while latency percentiles are computed from retained samples.

Raw JSON reports, signature pools, logs and local environment snapshots are intentionally excluded from this curated publication package.

## Key result

ML-DSA-65 verify throughput peaked at c8 in this run. Beyond c8, additional concurrency reduced throughput and increased tail latency. All measured points completed with zero worker errors.
