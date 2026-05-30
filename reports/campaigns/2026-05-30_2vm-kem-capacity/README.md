# 2VM KEM Capacity Campaign — 2026-05-30

This directory contains a curated publication package for a two-VM KEM capacity campaign.

## Included profiles

- ML-KEM-768
- Hybrid ML-KEM + FrodoKEM-976-SHAKE
- Hybrid ML-KEM + HQC-256
- Classic McEliece 460896

## Contents

- `report/kem_campaign_report.md` — consolidated campaign report
- `summaries/kem_campaign_summary.csv` — all included datapoints
- `summaries/kem_campaign_c8_comparison.csv` — c8 comparison table
- `figures/*.png` and `figures/*.svg` — generated comparison figures
- `manifest.json` and `manifest.sha256` — campaign-level manifest

## Scope note

The cryptographic capacity harness was executed inside the SERVER VM container.
The LOADGEN VM was used for network sanity and monitoring baseline, not as the cryptographic load driver.

Classic McEliece was intentionally kept to a cautious c1/c8 baseline.
