# 3VM native OpenSSL ML-KEM Phase 2 c8 concurrency benchmark

Purpose: compare classical TLS 1.3 X25519 against hybrid TLS 1.3 X25519MLKEM768 under low concurrency.

Path:

    LOADGEN -> HAProxy/GATEWAY -> BACKEND /delay/N

Mode:

- Fresh TCP connection per request
- Fresh TLS 1.3 handshake per request
- No session reuse requested
- HTTP/1.1
- Connection: close
- curl worker based closed-loop execution
- concurrency: 8
- 400 requests per backend delay value

Backend delay values:

- 0 ms
- 10 ms
- 50 ms

This Phase 2 c8 run is an initial low-concurrency benchmark, not a maximum capacity test.
