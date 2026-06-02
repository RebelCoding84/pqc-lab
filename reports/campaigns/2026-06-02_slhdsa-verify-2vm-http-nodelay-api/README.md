# SLH-DSA 2VM HTTP/TCP_NODELAY verify API baseline

## Scope

This campaign measures a 2VM API path:

`LOADGEN VM -> HTTP/1.1 keep-alive + TCP_NODELAY -> SERVER VM -> liboqs verify -> response`

This is not a raw local crypto loop benchmark.

## Algorithm

- Provider: `real_slhdsa`
- Resolved algorithm: `SPHINCS+-SHA2-128f-simple`
- SERVER VM: `pqc-fedora-vm-baseline`
- LOADGEN VM: `pqc-fedora-vm-loadgen`
- Warmup: `2.0` s
- Duration: `20.0` s
- Repeats: `3`
- TCP_NODELAY: `True`

## Key result

- Highest mean throughput: c128, 7468.35 req/s
- Practical low-latency saturated point: c8, 7072.13 req/s, client P99 1.733 ms
- Errors: 0 across all included concurrency levels
- Client >100 ms samples: 0
- Client >1000 ms samples: 0

## Summary

| c | req/s mean | stdev | client P99 ms | server P99 ms | errors |
|---:|---:|---:|---:|---:|---:|
| 1 | 1815.55 | 6.81 | 0.601 | 0.354 | 0 |
| 8 | 7072.13 | 34.75 | 1.733 | 0.750 | 0 |
| 16 | 6981.07 | 98.27 | 4.278 | 1.812 | 0 |
| 32 | 7176.80 | 47.29 | 9.308 | 3.959 | 0 |
| 64 | 7329.38 | 182.99 | 19.341 | 7.473 | 0 |
| 128 | 7468.35 | 159.55 | 39.609 | 15.619 | 0 |


## Interpretation

c64 and c128 are included as saturation-extension points. They are useful for identifying the throughput ceiling and tail-latency behavior, not necessarily as recommended operating points.
