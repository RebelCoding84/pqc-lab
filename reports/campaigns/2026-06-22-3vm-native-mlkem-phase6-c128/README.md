# 3VM native OpenSSL ML-KEM Phase 6 c128 concurrency benchmark

Purpose: compare classical TLS 1.3 X25519 against hybrid TLS 1.3 X25519MLKEM768 under c128 concurrency with lightweight VM monitoring.

Path:

    LOADGEN -> HAProxy/GATEWAY -> BACKEND /delay/N

Mode:

- Fresh TCP connection per request
- Fresh TLS 1.3 handshake per request
- No session reuse requested
- HTTP/1.1
- Connection: close
- curl worker based closed-loop execution
- concurrency: 128
- 6400 requests per backend delay value

Backend delay values:

- 0 ms
- 10 ms
- 50 ms

Monitoring:

- LOADGEN, GATEWAY and BACKEND sampled once per second
- load average
- memory available
- established sockets
- TIME_WAIT sockets
- SYN_RECV sockets
- curl process count
- HAProxy process/file-descriptor count
