# SLH-DSA Verify-Capacity Analysis

## Executive Summary
This document summarizes the SLH-DSA coarse verify-capacity sweep on this host using the real OQS-backed provider path. Throughput scales from `c1` to a near-peak at `c32`, then enters overload/queueing behavior at `c64-c128` with sharply rising tail latency.

## Environment And Context
- Runtime mode: real provider (`provider=real_slhdsa`) with OQS opt-in environment.
- High-level algorithm class: `SLH-DSA`.
- Resolved OQS mechanism in this dataset: `SPHINCS+-SHA2-128f-simple`.
- Dataset location: `reports/capacity/slhdsa_verify/`.
- Measured coarse sweep points: `1, 8, 16, 32, 64, 128`.

## Benchmark Methodology Summary
- Operation: verify only (`operation=verify`).
- Signature pool: `fixtures/signatures/slhdsa_verify_pool_10000.jsonl`.
- Profile shape: `warmup_s=3`, `duration_s=20`, `repeats=3`.
- Report model: same verify-capacity harness/summary/CPU telemetry and algorithm-fact schema used for ML-DSA.

## Coarse Sweep Metrics

| concurrency | verify_per_sec_mean | p99_ms_mean | process_cpu_percent_avg_mean | process_cpu_percent_peak_max | system_cpu_percent_avg_mean | system_cpu_percent_peak_max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 3218.709260680938 | 0.32414642333302857 | 99.94333333333334 | 102.0 | 3.183333333333334 | 3.8 |
| 8 | 22850.930173000503 | 0.37684633328656975 | 798.7800000000002 | 799.8 | 24.46500000000001 | 25.7 |
| 16 | 34451.10493424243 | 0.6527341835499102 | 1592.726666666667 | 1599.5 | 48.85250000000001 | 51.7 |
| 32 | 39476.7975537827 | 1.3665093330958624 | 3119.0800000000004 | 3199.2 | 97.50083333333333 | 100.0 |
| 64 | 38785.7666911194 | 7.663786733476934 | 3036.1091666666666 | 3121.7 | 94.66083333333333 | 100.0 |
| 128 | 37440.4384107328 | 17.635660480200357 | 2783.526225820963 | 2965.1 | 86.59410706252814 | 88.5 |

## Algorithm Facts
- `resolved_algorithm`: `SPHINCS+-SHA2-128f-simple`
- `public_key_size_bytes`: `32`
- `secret_key_size_bytes`: `64`
- `signature_size_bytes`: `17088`

## Interpretation
- SLH-DSA scales much farther in concurrency than ML-DSA before peaking on this host.
- `c32` appears to be the peak / near-peak operating point (`~39.48k verify/s`) for this coarse sweep.
- CPU behavior is strongly compute-driven: process CPU average rises from `~100%` (`c1`) to `~3119%` (`c32`), and system CPU reaches near-full host saturation at `c32-c64`.
- `c64-c128` shows overload/queueing behavior: throughput flattens/slips (`~38.79k` to `~37.44k`) while `p99` rises sharply (`~7.66 ms` to `~17.64 ms`).
- Signature payload size is very large relative to ML-DSA (`17088 B` vs `3309 B`), which is operationally significant for transport, buffering, and edge capacity sizing.
