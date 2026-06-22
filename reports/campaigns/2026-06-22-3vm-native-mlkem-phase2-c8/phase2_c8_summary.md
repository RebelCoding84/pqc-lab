# Phase 2 c8 concurrency benchmark summary

Mode: curl worker based closed-loop execution, concurrency 8, fresh TCP and TLS 1.3 handshake per request, HTTP/1.1, Connection: close.

## Summary table

| profile | delay_ms | count | HTTP codes | appconnect avg | appconnect p50 | appconnect p95 | appconnect p99 | total avg | total p50 | total p95 | total p99 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X25519 | 0 | 400 | ['200'] | 3.357 ms | 3.270 ms | 4.958 ms | 6.536 ms | 4.462 ms | 4.316 ms | 6.589 ms | 8.077 ms |
| X25519 | 10 | 400 | ['200'] | 2.172 ms | 2.073 ms | 2.740 ms | 3.535 ms | 12.898 ms | 12.793 ms | 13.575 ms | 14.374 ms |
| X25519 | 50 | 400 | ['200'] | 2.618 ms | 2.517 ms | 3.723 ms | 4.160 ms | 53.556 ms | 53.474 ms | 54.674 ms | 55.120 ms |
| X25519MLKEM768 | 0 | 400 | ['200'] | 3.577 ms | 3.395 ms | 5.637 ms | 6.136 ms | 4.730 ms | 4.544 ms | 6.941 ms | 8.001 ms |
| X25519MLKEM768 | 10 | 400 | ['200'] | 2.311 ms | 2.191 ms | 2.875 ms | 4.308 ms | 13.030 ms | 12.882 ms | 13.784 ms | 15.096 ms |
| X25519MLKEM768 | 50 | 400 | ['200'] | 2.959 ms | 2.821 ms | 4.160 ms | 4.777 ms | 53.972 ms | 53.889 ms | 55.174 ms | 55.727 ms |

## Hybrid minus classical delta

| delay_ms | appconnect avg delta | appconnect p99 delta | total avg delta | total p99 delta |
|---:|---:|---:|---:|---:|
| 0 | 0.220 ms | -0.400 ms | 0.268 ms | -0.076 ms |
| 10 | 0.138 ms | 0.773 ms | 0.132 ms | 0.722 ms |
| 50 | 0.341 ms | 0.617 ms | 0.417 ms | 0.607 ms |

## Interpretation

All requests returned HTTP 200. At c8, the hybrid X25519MLKEM768 path remains stable and shows only a small additional average latency compared with classical X25519. P99 differences remain around sub-millisecond scale in these low-concurrency closed-loop runs.
