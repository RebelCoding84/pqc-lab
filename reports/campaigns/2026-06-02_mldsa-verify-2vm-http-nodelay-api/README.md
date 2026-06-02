# ML-DSA 2VM HTTP/TCP_NODELAY verify API baseline

## Scope

This campaign measures a 2VM API path:

`LOADGEN VM -> HTTP/1.1 keep-alive + TCP_NODELAY -> SERVER VM -> liboqs verify -> response`

This is not a raw local crypto loop benchmark.

## Algorithm

- Provider: `real_mldsa`
- Resolved algorithm: `ML-DSA-65`
- SERVER VM: `pqc-fedora-vm-baseline`
- LOADGEN VM: `pqc-fedora-vm-loadgen`
- Warmup: `2.0` s
- Duration: `20.0` s
- Repeats: `3`
- TCP_NODELAY: `True`

## Key result

- Highest mean throughput: c128, 7358.48 req/s
- Practical low-latency saturated point: c8, 6971.68 req/s, client P99 2.175 ms
- Errors: 0 across all included concurrency levels
- Client >100 ms samples: 0
- Client >1000 ms samples: 0

## Summary

| c | req/s mean | stdev | client P99 ms | server P99 ms | errors |
|---:|---:|---:|---:|---:|---:|
| 1 | 4046.75 | 6.95 | 0.271 | 0.047 | 0 |
| 8 | 6971.68 | 101.23 | 2.175 | 0.842 | 0 |
| 16 | 6944.63 | 23.34 | 4.832 | 2.130 | 0 |
| 32 | 7230.88 | 42.11 | 10.044 | 4.582 | 0 |
| 64 | 7231.35 | 115.03 | 20.282 | 9.241 | 0 |
| 128 | 7358.48 | 176.95 | 40.351 | 17.740 | 0 |


## Interpretation

c64 and c128 are included as saturation-extension points. They are useful for identifying the throughput ceiling and tail-latency behavior, not necessarily as recommended operating points.
