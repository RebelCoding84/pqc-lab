# ML-DSA Verify-Capacity Single-VM Baseline — 2026-06-01

This directory contains a curated publication package for a single-node VM verify-capacity baseline.

## Included profile

- Algorithm: `ML-DSA-65`
- Provider: `real_mldsa`
- Operation: `verify`
- Pool size: 10,000 pre-generated signatures
- Warmup: 3 seconds
- Duration: 20 seconds
- Repeats: 3

## VM topology

- VM: `pqc-fedora-vm-baseline`
- Hypervisor: KVM/libvirt
- CPU mode: `host-passthrough`
- vCPU: 8
- Memory: 16 GiB
- Guest-visible topology: 1 socket × 8 cores × 1 thread
- Explicit vCPU pinning: no
- LOADGEN VM used: no

## Measured concurrency points

- c1
- c8
- c10
- c12
- c16
- c24
- c32

## Contents

- `report/*.md` — curated Markdown report
- `summaries/*.csv` — summary table for all measured points
- `figures/*.svg` — generated figures
- `monitoring/post_run_monitoring_summary.json` — post-run summary derived from benchmark JSON outputs
- `environment/vm_diagnostics.md` — curated VM diagnostics
- `manifest.json` and `manifest.sha256` — package-level manifest

## Scope note

This is a single-node VM verify-capacity baseline. Signing work is excluded from the measurement loop by using a pre-generated signature pool.

This package intentionally excludes raw JSON reports, signature pools, logs and full local environment/libvirt snapshots. The included VM diagnostics are curated to document the benchmark context without publishing full local VM metadata.

## Key result

Peak verify throughput was measured at c8: 73283.07 verify/s, with P99 latency 0.737662 ms. All measured points completed with zero worker errors.
