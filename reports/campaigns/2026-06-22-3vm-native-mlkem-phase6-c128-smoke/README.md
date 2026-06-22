# 3VM native OpenSSL ML-KEM Phase 6 c128 smoke benchmark

Purpose: small monitored c128 smoke test before full c128 benchmark.

Profile:

- X25519MLKEM768
- concurrency: 128
- backend delay: 0 ms
- total requests: 1280

Mode:

- Fresh TCP connection per request
- Fresh TLS 1.3 handshake per request
- No session reuse requested
- HTTP/1.1
- Connection: close
- curl worker based closed-loop execution

Path:

    LOADGEN -> HAProxy/GATEWAY -> BACKEND /delay/0
