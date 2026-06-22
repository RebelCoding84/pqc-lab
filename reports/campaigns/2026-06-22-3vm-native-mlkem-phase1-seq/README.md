# 3VM native OpenSSL ML-KEM Phase 1 sequential benchmark

Purpose: compare classical TLS 1.3 X25519 against hybrid TLS 1.3 X25519MLKEM768 in a 3VM HAProxy gateway path.

Path:

    LOADGEN -> HAProxy/GATEWAY -> BACKEND /delay/N

Mode:

- Fresh TCP connection per request
- Fresh TLS 1.3 handshake per request
- No session reuse requested
- HTTP/1.1
- Connection: close
- Sequential curl execution
- 200 requests per delay value

Backend delay values:

- 0 ms
- 10 ms
- 50 ms

This Phase 1 run is a sequential benchmark, not a concurrency/capacity benchmark. 
