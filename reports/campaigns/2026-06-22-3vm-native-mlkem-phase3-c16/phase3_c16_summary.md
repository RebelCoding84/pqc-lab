# Phase 3 c16 concurrency benchmark summary

Mode: curl worker based closed-loop execution, concurrency 16, fresh TCP and TLS 1.3 handshake per request, HTTP/1.1, Connection: close.

## Summary table

| profile | delay_ms | count | HTTP codes | appconnect avg | appconnect p50 | appconnect p95 | appconnect p99 | total avg | total p50 | total p95 | total p99 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X25519 | 0 | 800 | ['200'] | 6.322 ms | 5.870 ms | 11.416 ms | 14.061 ms | 8.354 ms | 8.008 ms | 13.454 ms | 15.561 ms |
| X25519 | 10 | 800 | ['200'] | 3.524 ms | 3.255 ms | 5.697 ms | 7.204 ms | 14.700 ms | 14.479 ms | 17.023 ms | 18.648 ms |
| X25519 | 50 | 800 | ['200'] | 2.351 ms | 2.187 ms | 3.288 ms | 5.074 ms | 53.195 ms | 53.019 ms | 54.333 ms | 56.576 ms |
| X25519MLKEM768 | 0 | 800 | ['200'] | 6.249 ms | 5.766 ms | 10.883 ms | 13.498 ms | 8.138 ms | 7.649 ms | 12.951 ms | 15.354 ms |
| X25519MLKEM768 | 10 | 800 | ['200'] | 3.426 ms | 3.160 ms | 5.444 ms | 7.824 ms | 14.533 ms | 14.288 ms | 16.920 ms | 19.117 ms |
| X25519MLKEM768 | 50 | 800 | ['200'] | 2.582 ms | 2.384 ms | 3.652 ms | 5.528 ms | 53.483 ms | 53.326 ms | 54.560 ms | 56.343 ms |

## Hybrid minus classical delta

| delay_ms | appconnect avg delta | appconnect p99 delta | total avg delta | total p99 delta |
|---:|---:|---:|---:|---:|
| 0 | -0.072 ms | -0.563 ms | -0.217 ms | -0.207 ms |
| 10 | -0.098 ms | 0.620 ms | -0.167 ms | 0.469 ms |
| 50 | 0.230 ms | 0.454 ms | 0.288 ms | -0.233 ms |

## Interpretation

All requests returned HTTP 200. At c16, both classical X25519 and hybrid X25519MLKEM768 remained stable. The observed latency differences are small and mostly within sub-millisecond scale, so this run does not show a meaningful instability or timeout penalty from the hybrid TLS 1.3 path at c16.
