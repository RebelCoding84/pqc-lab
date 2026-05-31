# ML-DSA vs SLH-DSA Verify-Capacity Single-Node Comparison

## Source packages

- `reports/campaigns/2026-05-31_mldsa-verify-single-node/`
- `reports/campaigns/2026-05-31_slhdsa-verify-single-node/`

## Scope note

This comparison uses two curated single-node local host verify-capacity baselines. No separate SERVER/LOADGEN VM topology was used in either baseline.

Both measurements exclude signing work from the verify loop by using pre-generated signature pools.

Latency comparability caveat: the ML-DSA high-throughput points hit the latency sampling cap, while the SLH-DSA points did not. Throughput is based on total operation counts in both runs; latency percentiles are computed from retained samples.

## Peak comparison

| metric | ML-DSA-65 | SLH-DSA / SPHINCS+-SHA2-128f-simple | ratio |
|---|---:|---:|---:|
| peak concurrency | c8 | c32 | — |
| peak verify/s mean | 265946.59 | 36294.84 | ML-DSA 7.33x SLH-DSA |
| P99 latency at peak | 0.040860 ms | 1.026890 ms | SLH-DSA 25.13x ML-DSA |

## Common concurrency points

| c | ML-DSA verify/s | SLH-DSA verify/s | ML/SLH throughput | ML-DSA P99 ms | SLH-DSA P99 ms | SLH/ML P99 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37442.38 | 3212.33 | 11.66x | 0.027993 | 0.326683 | 11.67x |
| 8 | 265946.59 | 22759.92 | 11.68x | 0.040860 | 0.379915 | 9.30x |
| 16 | 205061.76 | 32941.02 | 6.23x | 0.235016 | 0.615090 | 2.62x |
| 32 | 137449.19 | 36294.84 | 3.79x | 0.927769 | 1.026890 | 1.11x |

## Key observations

- ML-DSA-65 peak throughput was `265946.59` verify/s at `c8`.
- SLH-DSA/SPHINCS+-SHA2-128f-simple peak throughput was `36294.84` verify/s at `c32`.
- Peak-to-peak, ML-DSA delivered `7.33x` the verify throughput of SLH-DSA in these single-node local host runs.
- ML-DSA reached its practical knee earlier, at `c8` in its baseline.
- SLH-DSA scaled to a higher concurrency point, with practical peak at `c32`, but with much lower absolute throughput.
- In both baselines, worker errors stayed at zero; operational saturation is visible in tail latency before outright failures.

## Practical interpretation

The comparison highlights two different operational profiles. ML-DSA-65 is much faster in absolute verify throughput, but its best operating point appears earlier. SLH-DSA/SPHINCS+-SHA2-128f-simple is slower, but continues scaling to a higher concurrency point before tail latency becomes the dominant warning signal.

For infrastructure planning, the result reinforces that post-quantum migration is not just an algorithm-replacement question. Algorithm family, concurrency, queueing behavior and tail latency all affect real capacity planning.
