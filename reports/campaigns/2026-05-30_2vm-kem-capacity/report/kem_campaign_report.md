# 2VM KEM Capacity Campaign Report

- Campaign ID: `2vm-kem-capacity-campaign-20260530`
- Combined dataset SHA-256: `a691d8c322dcd2a5d43569a8df575d5c4ea8f62eb4e0955d2c4689444c61b306`
- Topology: Fedora host + two Fedora KVM VMs
- Execution note: cryptographic capacity harness was executed inside the SERVER VM container. LOADGEN VM was used for network sanity and monitoring baseline, not as the cryptographic load driver.
- Percentiles: P50/P95/P99/P99.9 latency in milliseconds. Throughput in handshakes per second.

## Tested profiles

- ML-KEM-768 — c1/c8/c32/c64/c128 — run `2vm-algorithm-baseline-20260526_054841`
- Hybrid ML-KEM + FrodoKEM — c1/c8/c32/c64 — run `2vm-hybrid-mlkem-frodo-20260530_024555`
- Hybrid ML-KEM + HQC-256 — c1/c8/c32/c64 — run `2vm-hybrid-mlkem-hqc-20260530_033828`
- Classic McEliece 460896 — c1/c8 cautious baseline — run `2vm-classic-mceliece-20260530_042759`

## Combined summary

| algorithm | concurrency | throughput mean hs/s | p50 ms | p95 ms | p99 ms | p99.9 ms | max latency ms | failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Classic McEliece 460896 | 1 | 15.65 | 56.5592 | 95.5584 | 123.1903 | 151.4509 | 169.5635 | 0 |
| Classic McEliece 460896 | 8 | 114.56 | 66.5482 | 107.8605 | 134.2600 | 174.4542 | 238.8781 | 0 |
| Hybrid ML-KEM + FrodoKEM | 1 | 257.15 | 3.8551 | 3.9378 | 4.0178 | 4.2173 | 4.5850 | 0 |
| Hybrid ML-KEM + FrodoKEM | 8 | 1847.83 | 4.2694 | 4.5126 | 4.6782 | 5.2013 | 14.0361 | 0 |
| Hybrid ML-KEM + FrodoKEM | 32 | 1310.61 | 22.6715 | 43.9020 | 55.5644 | 70.4219 | 110.3867 | 0 |
| Hybrid ML-KEM + FrodoKEM | 64 | 1439.89 | 40.4637 | 89.8229 | 116.9089 | 150.9819 | 263.9372 | 0 |
| Hybrid ML-KEM + HQC-256 | 1 | 34.52 | 28.9089 | 29.0580 | 29.3322 | 30.1041 | 31.0473 | 0 |
| Hybrid ML-KEM + HQC-256 | 8 | 257.62 | 30.9645 | 31.1318 | 31.3534 | 33.2016 | 50.9584 | 0 |
| Hybrid ML-KEM + HQC-256 | 32 | 256.25 | 124.0294 | 168.1722 | 196.8859 | 237.7186 | 288.5099 | 0 |
| Hybrid ML-KEM + HQC-256 | 64 | 256.67 | 243.8426 | 365.4125 | 437.9001 | 535.8152 | 773.2413 | 0 |
| ML-KEM-768 | 1 | 24909.06 | 0.0301 | 0.0471 | 0.0536 | 0.0618 | 0.5180 | 0 |
| ML-KEM-768 | 8 | 13166.71 | 0.5060 | 1.1746 | 1.5753 | 2.1036 | 4.0492 | 0 |
| ML-KEM-768 | 32 | 11678.38 | 2.3008 | 6.1079 | 8.3481 | 11.3076 | 21.0309 | 0 |
| ML-KEM-768 | 64 | 11613.43 | 4.5418 | 12.4063 | 17.1285 | 23.1892 | 41.2292 | 0 |
| ML-KEM-768 | 128 | 11242.08 | 10.5591 | 24.8605 | 33.3562 | 44.9773 | 86.9053 | 0 |

## c8 comparison

| algorithm | throughput mean hs/s | p99.9 ms | max latency ms | relative throughput vs ML-KEM c8 |
|---|---:|---:|---:|---:|
| ML-KEM-768 | 13166.71 | 2.10 | 4.05 | 1.0000x |
| Hybrid ML-KEM + FrodoKEM | 1847.83 | 5.20 | 14.04 | 0.1403x |
| Hybrid ML-KEM + HQC-256 | 257.62 | 33.20 | 50.96 | 0.0196x |
| Classic McEliece 460896 | 114.56 | 174.45 | 238.88 | 0.0087x |

## Key observations

- At c8, ML-KEM-768 reached `13166.71` hs/s, while Hybrid ML-KEM + FrodoKEM reached `1847.83` hs/s.
- At c8, Frodo hybrid throughput was about `7.2x` higher than HQC hybrid throughput.
- At c8, HQC hybrid throughput was about `2.2x` higher than Classic McEliece throughput.
- All included full-sweep datapoints completed with zero failures.
- The main operational pattern is that higher concurrency can preserve apparent success while tail latency grows sharply. This is clearest in the Frodo and HQC c32/c64 points.
- Classic McEliece was intentionally kept to a cautious c1/c8 baseline and should not be interpreted as a saturation study.

## Practical interpretation

This campaign shows why PQC readiness cannot be evaluated only by checking whether an algorithm works. The more operationally relevant question is where throughput stops improving and tail latency starts to dominate. In this VM/container setup, c8 is a practical knee point for the heavier profiles. Beyond that, additional concurrency often produces little or no throughput benefit while increasing P99/P99.9 latency substantially.
