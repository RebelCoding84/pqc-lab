# Phase 1 sequential benchmark summary

Profiles:

- `X25519` classical TLS 1.3
- `X25519MLKEM768` hybrid TLS 1.3

Mode:

- Fresh TCP connection per request
- Fresh TLS 1.3 handshake per request
- No session reuse requested
- HTTP/1.1
- `Connection: close`
- Sequential curl execution
- 200 requests per backend delay value

## Summary table

| profile | delay_ms | count | HTTP codes | appconnect avg | appconnect p50 | appconnect p95 | appconnect p99 | total avg | total p50 | total p95 | total p99 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X25519 | 0 | 200 | ['200'] | 2.075 ms | 1.943 ms | 2.540 ms | 2.829 ms | 2.703 ms | 2.538 ms | 3.291 ms | 3.611 ms |
| X25519 | 10 | 200 | ['200'] | 2.498 ms | 2.502 ms | 2.997 ms | 3.246 ms | 13.451 ms | 13.490 ms | 14.101 ms | 14.326 ms |
| X25519 | 50 | 200 | ['200'] | 2.778 ms | 2.729 ms | 3.220 ms | 3.356 ms | 54.094 ms | 54.067 ms | 54.669 ms | 55.140 ms |
| X25519MLKEM768 | 0 | 200 | ['200'] | 2.237 ms | 2.092 ms | 2.719 ms | 3.014 ms | 2.877 ms | 2.708 ms | 3.479 ms | 3.761 ms |
| X25519MLKEM768 | 10 | 200 | ['200'] | 2.650 ms | 2.660 ms | 3.207 ms | 3.349 ms | 13.656 ms | 13.712 ms | 14.285 ms | 14.350 ms |
| X25519MLKEM768 | 50 | 200 | ['200'] | 3.075 ms | 3.003 ms | 3.543 ms | 3.887 ms | 54.495 ms | 54.441 ms | 55.211 ms | 55.615 ms |

## Hybrid minus classical delta

| delay_ms | appconnect avg delta | appconnect p99 delta | total avg delta | total p99 delta |
|---:|---:|---:|---:|---:|
| 0 | 0.162 ms | 0.185 ms | 0.173 ms | 0.150 ms |
| 10 | 0.152 ms | 0.103 ms | 0.205 ms | 0.024 ms |
| 50 | 0.297 ms | 0.531 ms | 0.401 ms | 0.475 ms |

## Interpretation

All requests returned HTTP 200. Backend delay is reflected correctly in total request time. In this sequential Phase 1 benchmark, the hybrid `X25519MLKEM768` TLS 1.3 path adds a small but measurable handshake/total-time cost compared with classical `X25519`. The observed total-time P99 delta remains below 0.5 ms in all tested backend-delay cases; the largest appconnect P99 delta was 0.531 ms at the 50 ms backend-delay case.
