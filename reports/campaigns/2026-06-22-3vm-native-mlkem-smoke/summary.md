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

It does not yet prove full proxying through GATEWAY -> BACKEND. The backend delay service is already running separately on BACKEND port `18081`, and GATEWAY/LOADGEN connectivity to it has been verified.
