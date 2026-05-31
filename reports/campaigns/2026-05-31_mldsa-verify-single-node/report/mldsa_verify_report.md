# ML-DSA Verify-Capacity Single-Node Baseline

- Run ID: `single-node-mldsa-verify-20260531_043126`
- Operation: `verify`
- Provider: `real_mldsa`
- Resolved algorithm: `ML-DSA-65`
- Pool size: `10000` pre-generated signatures
- Warmup: `3 s`
- Duration: `20 s`
- Repeats: `3`
- Repo branch: `experiment/verify-capacity-single-node-20260531`
- Repo commit: `f323ef7`

## Scope note

This is a single-node verify-capacity baseline. Signing work is excluded from the measurement loop by using a pre-generated signature pool.

At high-throughput points, latency sampling may hit the runner cap. Throughput is based on total operation counts, while latency percentiles are computed from retained samples.

## Summary table

| c | verify/s mean | stdev | p50 ms | p95 ms | p99 ms | max ms | errors | in-flight max | latency truncated |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 37442.38 | 40.42 | 0.026303 | 0.026650 | 0.027993 | 0.536124 | 0 | 1 | False |
| 8 | 265946.59 | 1771.11 | 0.028844 | 0.033054 | 0.040860 | 2.314998 | 0 | 8 | True |
| 10 | 238578.46 | 4190.95 | 0.039427 | 0.058343 | 0.076554 | 2.985895 | 0 | 10 | True |
| 12 | 225776.98 | 688.54 | 0.050481 | 0.082898 | 0.111277 | 2.069048 | 0 | 12 | True |
| 16 | 205061.76 | 11920.66 | 0.069730 | 0.158871 | 0.235016 | 1.460723 | 0 | 16 | True |
| 24 | 143196.19 | 1631.97 | 0.164378 | 0.436807 | 0.619545 | 2.169208 | 0 | 24 | True |
| 32 | 137449.19 | 662.05 | 0.227475 | 0.632625 | 0.927769 | 2.813094 | 0 | 32 | True |

## Key observations

- Best measured throughput was at `c8`: `265946.59` verify/s.
- `c8` is the practical knee in this run: `265946.59` verify/s with P99 latency `0.040860` ms.
- `c10` vs `c8`: throughput `0.897x`, P99 latency `1.87x`.
- `c12` vs `c8`: throughput `0.849x`, P99 latency `2.72x`.
- `c16` vs `c8`: throughput `0.771x`, P99 latency `5.75x`.
- `c24` vs `c8`: throughput `0.538x`, P99 latency `15.16x`.
- `c32` vs `c8`: throughput `0.517x`, P99 latency `22.71x`.
- At `c32`, throughput fell to `0.517x` of `c8`, while P99 latency rose to `22.71x` of `c8`.
- All measured points completed with `worker_errors_sum = 0`; success/failure counts alone would hide the saturation behavior.

## Practical interpretation

ML-DSA-65 verify throughput peaks at `c8` in this single-node run. Beyond `c8`, additional concurrency does not improve capacity. Instead, throughput declines and tail latency widens. `c24` and `c32` characterize saturation/queueing rather than useful low-latency production operating points.
