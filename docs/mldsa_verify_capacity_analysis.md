# ML-DSA Verify-Capacity Analysis

## Executive Summary
This document summarizes real ML-DSA verify-capacity results from the existing audit dataset under `reports/capacity/mldsa_verify/`. On this host, throughput peaks near concurrency `c8`, then declines through `c10-c24`, and finally stabilizes in a saturated regime from `c32` onward. Tail latency (`p99`) rises sharply after `c8`, while `worker_errors_sum` remains `0` at all measured points.

## Environment And Context
- Campaign branch: `campaign-f38-baremetal-2026-03-01`
- Runtime mode: real provider (`provider=real_mldsa`) with OQS opt-in environment
- Resolved mechanism in reports: `ML-DSA-65`
- Dataset location: `reports/capacity/mldsa_verify/`
- Measured points: `1, 8, 10, 12, 16, 24, 32, 64, 128`

## Benchmark Methodology Summary
- Operation: verify only (`operation=verify`)
- Signature pool: `fixtures/signatures/mldsa_verify_pool_10000.jsonl`
- Profile shape: `warmup_s=3`, `duration_s=20`, `repeats=3`
- Report interpretation source: JSON `summary` fields

## Measured Points
Concurrency points measured in this dataset:
`1, 8, 10, 12, 16, 24, 32, 64, 128`

| concurrency | verify_per_sec_mean | p50_ms_mean | p95_ms_mean | p99_ms_mean | max_ms_max |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 37396.90254016156 | 0.02633433329416827 | 0.026760333336521096 | 0.027846666701710394 | 0.576884000111022 |
| 8 | 266952.60923477705 | 0.02893699987301564 | 0.03154333323133566 | 0.04048999987086669 | 2.674510999895574 |
| 10 | 236174.31308722604 | 0.03917399953934364 | 0.05979000040194175 | 0.07974433296112693 | 1.7735840010573156 |
| 12 | 226273.85433162836 | 0.05050066647527274 | 0.08481433330113457 | 0.11586066678622349 | 2.0928160001858487 |
| 16 | 213434.0027074984 | 0.06852366671713146 | 0.14359766676837657 | 0.21037800675912877 | 1.0407770005258499 |
| 24 | 146153.54622609145 | 0.1599643334581439 | 0.4307933334833554 | 0.6271017264013306 | 2.802310999868496 |
| 32 | 137252.44844227502 | 0.22735466685238256 | 0.6393514834144293 | 0.9944010965106524 | 3.4059649997288943 |
| 64 | 136215.9399703428 | 0.4606996661398928 | 1.3554269996044848 | 2.1864667702326797 | 6.86633300028916 |
| 128 | 136596.3206403944 | 0.9248869998070101 | 2.766787833555402 | 4.519687610081746 | 15.157085000282677 |

## Near-Linear Scaling Region
The strongest throughput growth occurs from `c1` to `c8`, ending at approximately `266,952.61 verify/s`. This region is the closest to near-linear scaling on this host.

## Knee Point
The knee starts shortly after `c8`. `c10` (`~236,174.31`) and `c12` (`~226,273.85`) confirm that throughput no longer improves, while latency percentiles begin widening.

## Contention Region
`c16` (`~213,434.00`) shows clear contention with further throughput reduction and increased tail latency relative to `c8-c12`.

## Saturation / Queueing Regime
`c24` marks transition toward saturation/queueing (`~146,153.55`). From `c32` through `c128`, throughput forms a stable overloaded ceiling (`~136k-146k verify/s`) while `p99` and `max` latencies continue to rise.

## Industrial Relevance
- For low-latency production sizing on this host, operate near the knee (`c8`, at most `c10`).
- Use `c24+` measurements for overload behavior characterization, not for low-latency target sizing.
- Zero `worker_errors_sum` across all points indicates stability under load, but latency/queueing still constrains practical operating windows.

## Conclusion
- Peak throughput is near `c8`.
- Practical operating window is around `c8` and at most `c10`.
- `c24+` is not a good low-latency production region on this host.
- `c32-c128` indicates a stable overloaded service ceiling around `~136k-146k verify/s`.

