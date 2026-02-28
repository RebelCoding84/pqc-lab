# Capacity Methodology (Publication Snapshot)

## Objective
Measure PQC key-exchange capacity under a concurrent burst workload and produce audit-friendly artifacts suitable for engineering review.

## Environment
- Host: Fedora Linux workstation (container runtime host).
- Execution container: `pqc-lab:pqc`.
- Provider path: liboqs.
- Python runtime in measurement container: `3.11.14`.

## Protocol
- Workload model: burst handshakes.
- Concurrency sweep: `1`, `8`, `32`, `128`.
- Measurement duration: `60` seconds per run.
- Warmup duration: `10` seconds per run (discarded).
- Repeats: `3` runs per profile/concurrency point.

## Metrics
- Throughput: handshakes per second.
- Latency: `p50`, `p95`, `p99`, and `max` per successful measurement window.
- CPU: average and peak CPU percent (best-effort sampling).
- Reliability: `failure_count`.

## Reproducibility
- Reports embed `git_commit` from `GIT_COMMIT`.
- The commit should be exported before execution so each artifact is traceable to an exact source snapshot.

## Limitations
- Container-level CPU percentage is best-effort telemetry and may not map perfectly to host scheduler behavior.
- Results are performance/capacity evidence and reproducibility evidence for this harness setup.
- Results are not a cryptographic security proof.
