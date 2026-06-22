# Phase 6 c128 concurrency benchmark summary

Mode: curl worker based closed-loop execution, concurrency 128, fresh TCP and TLS 1.3 handshake per request, HTTP/1.1, Connection: close.

## Summary table

| profile | delay_ms | count | ok | HTTP codes | appconnect avg | appconnect p50 | appconnect p95 | appconnect p99 | total avg | total p50 | total p95 | total p99 |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X25519 | 0 | 6400 | 6400 | ['200'] | 43.435 ms | 35.133 ms | 107.513 ms | 123.686 ms | 61.842 ms | 55.343 ms | 124.913 ms | 140.967 ms |
| X25519 | 10 | 6400 | 6400 | ['200'] | 36.365 ms | 28.730 ms | 98.579 ms | 130.942 ms | 58.246 ms | 49.707 ms | 119.577 ms | 155.139 ms |
| X25519 | 50 | 6400 | 6400 | ['200'] | 29.108 ms | 23.010 ms | 68.430 ms | 82.632 ms | 93.165 ms | 88.511 ms | 132.200 ms | 149.344 ms |
| X25519MLKEM768 | 0 | 6400 | 6400 | ['200'] | 43.812 ms | 33.229 ms | 113.373 ms | 135.725 ms | 61.391 ms | 53.051 ms | 131.560 ms | 157.202 ms |
| X25519MLKEM768 | 10 | 6400 | 6400 | ['200'] | 37.939 ms | 30.638 ms | 92.993 ms | 116.206 ms | 60.100 ms | 52.884 ms | 116.906 ms | 142.323 ms |
| X25519MLKEM768 | 50 | 6400 | 6400 | ['200'] | 28.420 ms | 23.080 ms | 66.421 ms | 83.470 ms | 93.102 ms | 89.260 ms | 132.243 ms | 149.782 ms |

## Hybrid minus classical delta

| delay_ms | appconnect avg delta | appconnect p99 delta | total avg delta | total p99 delta |
|---:|---:|---:|---:|---:|
| 0 | 0.377 ms | 12.039 ms | -0.451 ms | 16.235 ms |
| 10 | 1.574 ms | -14.736 ms | 1.854 ms | -12.816 ms |
| 50 | -0.687 ms | 0.838 ms | -0.063 ms | 0.438 ms |

## Monitor peaks

| file | rows | max load1 | min mem available KB | max established | max TIME_WAIT | max SYN_RECV | max curl count | max HAProxy FD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| monitor_loadgen_c128_classical_full.csv | 46 | 32.03 | 7221440 | 83 | 1 | 0 | 255 | 0 |
| monitor_gateway_c128_classical_full.csv | 51 | 0.2 | 15589884 | 141 | 340 | 0 | 0 | 156 |
| monitor_backend_c128_classical_full.csv | 52 | 0.12 | 7404084 | 49 | 9279 | 0 | 0 | 0 |
| monitor_loadgen_c128_hybrid_full.csv | 60 | 37.7 | 7253352 | 76 | 1 | 0 | 256 | 0 |
| monitor_gateway_c128_hybrid_full.csv | 64 | 0.41 | 15586720 | 144 | 299 | 1 | 0 | 167 |
| monitor_backend_c128_hybrid_full.csv | 65 | 0.49 | 7411116 | 54 | 9269 | 1 | 0 | 0 |

## Interpretation

All full c128 requests returned HTTP 200 for both classical X25519 and hybrid X25519MLKEM768. No timeout or connection-failure rows were observed.

At c128, tail latency is materially higher than at c64. Monitoring indicates the main pressure is on the LOADGEN side, where many curl workers and fresh TCP/TLS handshakes create scheduler and process-launch pressure. Gateway and backend load averages remained low, although TIME_WAIT counts rose as expected due to the large number of short-lived connections.

The hybrid path showed no clear instability or failure penalty versus classical X25519. Average total latency was very close between the two profiles. P99 latency varied by delay in both directions, which suggests closed-loop worker scheduling and VM/network path noise dominate precise tail-latency differences at this load level.
