# Phase 4 c32 concurrency benchmark summary

Mode: curl worker based closed-loop execution, concurrency 32, fresh TCP and TLS 1.3 handshake per request, HTTP/1.1, Connection: close.

## Summary table

| profile | delay_ms | count | HTTP codes | appconnect avg | appconnect p50 | appconnect p95 | appconnect p99 | total avg | total p50 | total p95 | total p99 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X25519 | 0 | 1600 | ['200'] | 11.543 ms | 9.811 ms | 24.523 ms | 27.917 ms | 15.600 ms | 14.112 ms | 27.994 ms | 31.283 ms |
| X25519 | 10 | 1600 | ['200'] | 8.541 ms | 7.517 ms | 16.830 ms | 19.724 ms | 21.864 ms | 21.166 ms | 30.571 ms | 33.931 ms |
| X25519 | 50 | 1600 | ['200'] | 2.516 ms | 2.173 ms | 4.143 ms | 7.486 ms | 53.469 ms | 53.088 ms | 55.589 ms | 60.279 ms |
| X25519MLKEM768 | 0 | 1600 | ['200'] | 11.886 ms | 9.973 ms | 25.212 ms | 28.196 ms | 16.202 ms | 14.840 ms | 29.156 ms | 32.726 ms |
| X25519MLKEM768 | 10 | 1600 | ['200'] | 8.472 ms | 7.426 ms | 17.038 ms | 19.895 ms | 21.781 ms | 20.958 ms | 30.749 ms | 34.111 ms |
| X25519MLKEM768 | 50 | 1600 | ['200'] | 2.606 ms | 2.321 ms | 3.888 ms | 5.821 ms | 53.514 ms | 53.220 ms | 54.959 ms | 57.885 ms |

## Hybrid minus classical delta

| delay_ms | appconnect avg delta | appconnect p99 delta | total avg delta | total p99 delta |
|---:|---:|---:|---:|---:|
| 0 | 0.343 ms | 0.279 ms | 0.602 ms | 1.443 ms |
| 10 | -0.069 ms | 0.171 ms | -0.083 ms | 0.180 ms |
| 50 | 0.090 ms | -1.665 ms | 0.046 ms | -2.394 ms |

## Interpretation

All requests returned HTTP 200. At c32, both classical X25519 and hybrid X25519MLKEM768 remained stable with no timeout or connection-failure rows. Tail latency increased compared with lower-concurrency runs, especially for low backend-delay cases, but the hybrid path did not show a clear instability penalty.
