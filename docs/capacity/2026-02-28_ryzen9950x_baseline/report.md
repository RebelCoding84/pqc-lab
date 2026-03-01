# PQC Capacity Benchmark Report

## Methodology
This dataset is generated from enterprise-proof capacity runs with fixed concurrency and repeat controls to support direct comparison across algorithm profiles.

- Workload profile: burst handshake model with per-handshake latency collection.
- Concurrency: `32` worker threads for enterprise-proof runs.
- Repeats: `3` full warmup+measurement cycles per profile.
- Percentiles: latency summaries include standard tail metrics with explicit `p99.9` reporting.
- CPU measurement: both process-level and system-level CPU series are sampled and summarized (average and peak), with load average and logical CPU context included in output.

## Results Overview
The dataset is organized across three algorithm classes:
- ML-KEM
- Hybrid ML-KEM+Frodo
- Hybrid ML-KEM+HQC

| Algorithm | Throughput | P99 | P99.9 | CPU Behaviour |
|-----------|-----------|-----|------|---------------|
| ML-KEM | TBD | TBD | TBD | TBD |
| Hybrid ML-KEM+Frodo | TBD | TBD | TBD | TBD |
| Hybrid ML-KEM+HQC | TBD | TBD | TBD | TBD |

## Observed Behaviour
Across profiles, scaling characteristics diverge as concurrency pressure increases:
- Throughput scaling differs by algorithm class, with lightweight profiles sustaining higher effective handshake rates before flattening.
- Queueing effects become visible as worker demand exceeds efficient scheduling capacity; this appears first in tail metrics before median latency moves substantially.
- Tail latency growth (`P99` and `P99.9`) is a primary stress indicator and increases faster for heavier hybrid operations.
- CPU saturation evidence is captured by system/process peak utilization trends and reduced marginal throughput gain at fixed higher concurrency.

## Interpretation
The measurements separate into two operational regimes:
- Compute-bound regime: added workers produce near-proportional throughput improvements while latency remains controlled.
- Orchestration-bound regime: scheduler contention and runnable-queue pressure dominate, causing diminishing throughput gains and accelerated tail-latency expansion.

This framing helps distinguish algorithmic compute cost from runtime orchestration overhead under load.

## Reproducibility
Reproducibility controls are built into execution and reporting:
- Runtime isolation through Docker (`pqc-lab:pqc` image).
- Dependency and toolchain consistency through Pixi-managed environments.
- Provenance metadata captured in report payloads, including `git_commit`, platform details, and benchmark configuration parameters.

Together, these controls support repeat runs, audit review, and cross-run comparability.

## Dataset Location
Primary dataset directories:
- `reports/capacity/`
- `reports/enterprise_proof/`
