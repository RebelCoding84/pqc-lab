# ML-DSA vs SLH-DSA Verify-Capacity Comparison

## Executive Summary
Using the same verify-capacity harness and telemetry schema, ML-DSA is much faster in absolute verify throughput, while SLH-DSA scales farther in concurrency before its peak. On this host, ML-DSA peaks at `c8` and then transitions to runtime/scheduler/concurrency-bound behavior, while SLH-DSA peaks near `c32` with much stronger CPU-bound characteristics before queueing dominates.

## Methodology Alignment
- Both datasets were produced with the same verify-capacity runner, report shape, repeat structure, and CPU telemetry model.
- Both include algorithm object-size facts copied from pool metadata.
- Because harness semantics are aligned, the two datasets are directly comparable for industrial capacity planning.

## Direct Comparison

| metric | ML-DSA | SLH-DSA |
| --- | --- | --- |
| resolved algorithm | `ML-DSA-65` | `SPHINCS+-SHA2-128f-simple` |
| public key size | `1952 B` | `32 B` |
| secret key size | `4032 B` | `64 B` |
| signature size | `3309 B` | `17088 B` |
| peak concurrency (coarse) | `c8` | `c32` |
| peak throughput (`verify_per_sec_mean`) | `267514.2768306771` | `39476.7975537827` |
| representative post-knee throughput points | `c16: 218179.45102980768`, `c32: 137262.3761169736`, `c64: 137636.90699398168` | `c8: 22850.930173000503`, `c16: 34451.10493424243`, `c64: 38785.7666911194`, `c128: 37440.4384107328` |
| representative p99 trend | `c8: 0.04049700002421256`, `c16: 0.2105180033125483`, `c32: 0.9959646999808077`, `c64: 2.1710007666729325` | `c8: 0.37684633328656975`, `c16: 0.6527341835499102`, `c32: 1.3665093330958624`, `c64: 7.663786733476934` |
| representative process CPU avg trend | `c8: 794.1424999999998`, `c16: 771.1983333333333`, `c32: 471.70750000000004`, `c64: 473.1166666666667` | `c8: 798.7800000000002`, `c16: 1592.726666666667`, `c32: 3119.0800000000004`, `c64: 3036.1091666666666` |
| dominant post-knee interpretation | Early knee; after `c8`, throughput drops while process CPU avg also drops, indicating runtime/scheduler/concurrency limits dominate. | Later knee; scaling continues to `c32` with sustained high CPU utilization, indicating stronger CPU-bound behavior before overload queueing. |
| overload / queueing behavior | Stable overloaded plateau by `c32-c64` with rising tails. | Overload/queueing is clear at `c64+`, with near-flat throughput and sharply higher tail latency. |

## Industrial Interpretation
- ML-DSA is far faster in absolute verify throughput on this host.
- ML-DSA peaks early (`c8`) and then behaves more like runtime/scheduler/concurrency-bound service capacity than pure CPU saturation.
- SLH-DSA is much slower in absolute throughput, but it scales farther in concurrency (`c32` peak/near-peak) and appears much more CPU-bound through its rise.
- Object-size trade-off is asymmetric: SLH-DSA has very small keys (`32 B` / `64 B`) but very large signatures (`17088 B`), while ML-DSA has larger keys (`1952 B` / `4032 B`) and much smaller signatures (`3309 B`) than SLH-DSA.
- For fallback-signature infrastructure planning, throughput cost is materially higher with SLH-DSA, but its concurrency behavior differs and should be capacity-modeled separately rather than extrapolated from ML-DSA knee behavior.
