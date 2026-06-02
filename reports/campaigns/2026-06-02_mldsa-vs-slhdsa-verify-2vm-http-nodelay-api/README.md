# ML-DSA vs SLH-DSA 2VM HTTP/TCP_NODELAY verify API comparison

## Scope

This comparison measures the same 2VM API path for both algorithms:

`LOADGEN VM -> HTTP/1.1 keep-alive + TCP_NODELAY -> SERVER VM -> liboqs verify -> response`

The comparison is API-path-bound at higher concurrency. c1 shows algorithm cost more clearly; c8+ increasingly shows service-path saturation.

## Summary

| c | ML-DSA req/s | SLH-DSA req/s | ML/SLH throughput | ML client P99 | SLH client P99 | ML server P99 | SLH server P99 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4046.75 | 1815.55 | 2.23x | 0.271 ms | 0.601 ms | 0.047 ms | 0.354 ms |
| 8 | 6971.68 | 7072.13 | 0.99x | 2.175 ms | 1.733 ms | 0.842 ms | 0.750 ms |
| 16 | 6944.63 | 6981.07 | 0.99x | 4.832 ms | 4.278 ms | 2.130 ms | 1.812 ms |
| 32 | 7230.88 | 7176.80 | 1.01x | 10.044 ms | 9.308 ms | 4.582 ms | 3.959 ms |
| 64 | 7231.35 | 7329.38 | 0.99x | 20.282 ms | 19.341 ms | 9.241 ms | 7.473 ms |
| 128 | 7358.48 | 7468.35 | 0.99x | 40.351 ms | 39.609 ms | 17.740 ms | 15.619 ms |


## Interpretation

- At c1, ML-DSA is materially faster than SLH-DSA in this API-path test.
- From c8 upward, both algorithms converge near the same HTTP API path saturation band around ~7k requests/s.
- c64/c128 are useful as saturation-extension points, not as recommended operating points.
