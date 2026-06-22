# Phase 5 c64 concurrency benchmark summary

Mode: curl worker based closed-loop execution, concurrency 64, fresh TCP and TLS 1.3 handshake per request, HTTP/1.1, Connection: close.

## Summary table

| profile | delay_ms | count | HTTP codes | appconnect avg | appconnect p50 | appconnect p95 | appconnect p99 | total avg | total p50 | total p95 | total p99 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X25519 | 0 | 3200 | ['200'] | 23.034 ms | 18.482 ms | 53.552 ms | 57.919 ms | 31.312 ms | 27.847 ms | 61.214 ms | 67.099 ms |
| X25519 | 10 | 3200 | ['200'] | 18.753 ms | 15.241 ms | 40.728 ms | 50.137 ms | 37.930 ms | 35.318 ms | 61.227 ms | 67.196 ms |
| X25519 | 50 | 3200 | ['200'] | 6.487 ms | 5.379 ms | 14.588 ms | 21.542 ms | 58.987 ms | 58.056 ms | 67.038 ms | 73.749 ms |
| X25519MLKEM768 | 0 | 3200 | ['200'] | 23.110 ms | 18.734 ms | 53.680 ms | 58.541 ms | 32.256 ms | 29.073 ms | 61.964 ms | 67.239 ms |
| X25519MLKEM768 | 10 | 3200 | ['200'] | 19.603 ms | 15.931 ms | 42.624 ms | 51.736 ms | 39.262 ms | 36.913 ms | 62.464 ms | 69.757 ms |
| X25519MLKEM768 | 50 | 3200 | ['200'] | 7.522 ms | 6.373 ms | 15.746 ms | 21.502 ms | 60.333 ms | 59.452 ms | 68.914 ms | 75.139 ms |

## Hybrid minus classical delta

| delay_ms | appconnect avg delta | appconnect p99 delta | total avg delta | total p99 delta |
|---:|---:|---:|---:|---:|
| 0 | 0.076 ms | 0.622 ms | 0.944 ms | 0.140 ms |
| 10 | 0.850 ms | 1.599 ms | 1.332 ms | 2.561 ms |
| 50 | 1.035 ms | -0.040 ms | 1.346 ms | 1.390 ms |

## Interpretation

All requests returned HTTP 200. At c64, both classical X25519 and hybrid X25519MLKEM768 remained stable with no timeout or connection-failure rows. Tail latency increased clearly compared with c32, which indicates scheduler/load-generator/gateway-path pressure from many fresh TCP and TLS handshakes. The hybrid path showed a small measurable overhead, but no instability or failure penalty in this run.
