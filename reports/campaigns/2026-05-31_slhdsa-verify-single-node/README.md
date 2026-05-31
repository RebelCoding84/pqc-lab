# SLH-DSA Verify-Capacity Single-Node Baseline — 2026-05-31

This directory contains a curated publication package for a single-node SLH-DSA verify-capacity baseline.

## Included profile

- Requested algorithm: SLH-DSA
- Resolved algorithm: SPHINCS+-SHA2-128f-simple
- Provider: `real_slhdsa`
- Operation: `verify`
- Pool size: 10,000 pre-generated signatures
- Warmup: 3 seconds
- Duration: 20 seconds
- Repeats: 3

## Measured concurrency points

- c1
- c8
- c16
- c32
- c64
- c128

## Contents

- `report/slhdsa_verify_report.md` — curated Markdown report
- `summaries/slhdsa_verify_summary.csv` — summary table for all measured points
- `figures/*.png` and `figures/*.svg` — generated figures
- `manifest.json` and `manifest.sha256` — package-level manifest

## Scope note

This is a single-node local host verify-capacity baseline. No separate SERVER/LOADGEN VM topology was used in this phase.

Signing work is excluded from the measurement loop by using a pre-generated signature pool.

Raw JSON reports, signature pools, logs, local environment snapshots and helper scripts are intentionally excluded from this curated publication package.

## Key result

SLH-DSA/SPHINCS+-SHA2-128f-simple verify throughput peaked at c32 in this run. Beyond c32, additional concurrency did not improve throughput meaningfully, while P99 latency increased sharply.
