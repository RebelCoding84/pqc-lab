# 3VM native ML-KEM TLS 1.3 smoke test

Date: 2026-06-22  
Repository: pqc-lab  
Campaign path: reports/campaigns/2026-06-22-3vm-native-mlkem-smoke

## Result

PASS.

A TLS 1.3 handshake from LOADGEN to GATEWAY successfully negotiated the hybrid post-quantum group:

- Negotiated TLS 1.3 group: `X25519MLKEM768`
- TLS protocol: `TLSv1.3`
- Cipher suite: `TLS_AES_256_GCM_SHA384`
- Provider source: OpenSSL native default provider
- OpenSSL version on gateway: `OpenSSL 3.5.4`
- OpenSSL version on loadgen: `OpenSSL 3.5.4`
- Certificate type for this smoke test: self-signed RSA test certificate

## 3VM roles

- LOADGEN: `pqc-fedora-vm-loadgen`, `192.168.122.100`
- GATEWAY: `pqc-fedora-vm-baseline`, `192.168.122.194`
- BACKEND: `pqc-fedora-vm-backend`, `192.168.122.99`

## Verified evidence

The captured `openssl s_client` output includes:

```text
Negotiated TLS1.3 group: X25519MLKEM768
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Protocol: TLSv1.3
Verify return code: 18 (self-signed certificate)
```

The self-signed certificate verification warning is expected in this smoke test and does not invalidate the TLS 1.3 group negotiation result.

## Scope

This smoke test proves the LOADGEN -> GATEWAY TLS 1.3 hybrid key exchange path.

At this initial direct OpenSSL smoke stage, full proxying through GATEWAY -> BACKEND was not yet proven. The later HAProxy full proxy smoke section below verifies the complete LOADGEN -> GATEWAY -> BACKEND path.

## HAProxy full proxy smoke

PASS.

A full 3VM proxy smoke test was completed after the initial direct OpenSSL smoke test.

Verified path:

    LOADGEN -> HAProxy/GATEWAY TLS 1.3 X25519MLKEM768 -> BACKEND /delay/50 -> HTTP 200 OK

Evidence confirms:

- TLS 1.3 negotiated group: `X25519MLKEM768`
- TLS protocol: `TLSv1.3`
- Cipher suite: `TLS_AES_256_GCM_SHA384`
- ALPN protocol: `http/1.1`
- HAProxy frontend: `pqc_tls_frontend`
- HAProxy backend: `backend_delay/backend1`
- Backend endpoint: `/delay/50`
- Backend response: `HTTP/1.1 200 OK`
- Backend JSON response included `delay_ms: 50`

The HAProxy log shows successful forwarding from LOADGEN to BACKEND through the TLS frontend:

    pqc_tls_frontend~ backend_delay/backend1 ... 200 ... "GET /delay/50 HTTP/1.1"

This proves that the gateway proxy path works with OpenSSL-native hybrid ML-KEM TLS 1.3 in front of the backend delay service.

## Classical X25519 baseline smoke

PASS.

A matching classical TLS 1.3 baseline smoke was completed with HAProxy configured for `X25519`.

Verified path:

    LOADGEN -> HAProxy/GATEWAY TLS 1.3 X25519 -> BACKEND /delay/50 -> HTTP 200 OK

Evidence confirms:

- TLS protocol: `TLSv1.3`
- Classical key exchange evidence: `Peer Temp Key: X25519, 253 bits`
- Cipher suite: `TLS_AES_256_GCM_SHA384`
- ALPN protocol: `http/1.1`
- Backend endpoint: `/delay/50`
- Backend response: `HTTP/1.1 200 OK`
- Backend JSON response included `delay_ms: 50`

## Sequential timing calibration

PASS.

A small sequential curl calibration was run for both `X25519` and `X25519MLKEM768`.

This was not a capacity or deadline benchmark. It was a sanity check to verify that the measurement path behaves logically before larger load tests.

Summary from 10 requests per delay value:

    profile,delay_ms,count,http_codes,appconnect_avg_ms,total_avg_ms
    X25519,0,10,['200'],2.741,3.579
    X25519,10,10,['200'],2.548,13.594
    X25519,50,10,['200'],2.883,54.207
    X25519MLKEM768,0,10,['200'],2.825,3.646
    X25519MLKEM768,10,10,['200'],2.689,13.673
    X25519MLKEM768,50,10,['200'],3.154,54.513

Observed hybrid-minus-classical deltas in this small sequential smoke:

    delay=0 appconnect_delta=0.084 ms total_delta=0.067 ms
    delay=10 appconnect_delta=0.141 ms total_delta=0.080 ms
    delay=50 appconnect_delta=0.271 ms total_delta=0.306 ms

Interpretation: all requests returned HTTP 200, backend delay was reflected correctly in total request time, and the hybrid ML-KEM path showed only a small additional sequential handshake/total-time cost in this smoke check.
