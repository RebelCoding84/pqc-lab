# Phase 6 c128 smoke summary

Mode: monitored c128 smoke run, X25519MLKEM768, delay 0 ms, 1280 requests.

| profile | delay_ms | count | ok | HTTP codes | appconnect avg | appconnect p99 | total avg | total p99 |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| X25519MLKEM768 | 0 | 1280 | 1280 | ['200'] | 41.000 ms | 119.626 ms | 59.966 ms | 139.049 ms |

Interpretation: the c128 smoke run completed with HTTP 200 for all requests and justified proceeding to the full monitored c128 benchmark.
