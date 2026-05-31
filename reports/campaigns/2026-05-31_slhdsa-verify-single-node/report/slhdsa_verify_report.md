# SLH-DSA Verify-Capacity Single-Node Baseline

- Run ID: `single-node-slhdsa-verify-20260531_053747`
- Operation: `verify`
- Provider: `real_slhdsa`
- Resolved algorithm: `SPHINCS+-SHA2-128f-simple`
- Pool size: `10000` pre-generated signatures
- Warmup: `3 s`
- Duration: `20 s`
- Repeats: `3`
- Repo branch: `experiment/slhdsa-verify-single-node-20260531`
- Repo commit: `e6baa4f`

## Scope note

This is a single-node local host verify-capacity baseline. No separate SERVER/LOADGEN VM topology was used in this phase.

Signing work is excluded from the measurement loop by using a pre-generated signature pool. Throughput is reported as verify operations per second. Latency values are reported in milliseconds.

## Summary table

| c | verify/s mean | stdev | p50 ms | p95 ms | p99 ms | max ms | errors | in-flight max | latency truncated |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 3212.33 | 3.61 | 0.310623 | 0.320730 | 0.326683 | 0.824308 | 0 | 1 | False |
| 8 | 22759.92 | 70.95 | 0.349550 | 0.368523 | 0.379915 | 3.618141 | 0 | 8 | False |
| 16 | 32941.02 | 367.43 | 0.484408 | 0.538272 | 0.615090 | 4.509619 | 0 | 16 | False |
| 32 | 36294.84 | 68.99 | 0.869377 | 0.968535 | 1.026890 | 11.873844 | 0 | 32 | False |
| 64 | 35798.65 | 291.66 | 0.918205 | 5.343887 | 8.242928 | 27.805002 | 0 | 64 | False |
| 128 | 34565.40 | 65.88 | 1.556238 | 12.335572 | 19.162849 | 66.950504 | 0 | 128 | False |

## Key observations

- Best measured throughput was at `c32`: `36294.84` verify/s.
- `c32` is the practical peak in this run: `36294.84` verify/s with P99 latency `1.026890` ms.
- `c64` retained `0.986x` of `c32` throughput, while P99 latency increased to `8.03x` of `c32`.
- `c128` retained `0.952x` of `c32` throughput, while P99 latency increased to `18.66x` of `c32`.
- `c8` vs `c1`: throughput `7.085x`, P99 latency `1.16x`.
- `c16` vs `c1`: throughput `10.255x`, P99 latency `1.88x`.
- `c32` vs `c1`: throughput `11.299x`, P99 latency `3.14x`.
- `c64` vs `c1`: throughput `11.144x`, P99 latency `25.23x`.
- `c128` vs `c1`: throughput `10.760x`, P99 latency `58.66x`.
- All measured points completed with `worker_errors_sum = 0`; operational saturation appears in tail latency before outright failures.
- No measured point hit the latency sampling cap in this SLH-DSA run.

## Practical interpretation

SLH-DSA/SPHINCS+-SHA2-128f-simple verify throughput scales up to `c32` in this single-node run. Beyond `c32`, additional concurrency does not improve throughput meaningfully. `c64` and `c128` characterize saturation/queueing: throughput remains near the peak while P99 latency increases sharply.

This behavior differs from the ML-DSA run, where the practical knee appeared earlier at `c8`. SLH-DSA is slower in absolute throughput, but its peak appears at a higher concurrency level.
