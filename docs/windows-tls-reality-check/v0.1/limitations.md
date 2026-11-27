# Study limitations and interpretation boundaries

1. **Build support:** Windows 11 Insider Preview build 26320.9876 exhibited working hybrid TLS negotiation in the laboratory. This does **not** establish Microsoft support or production readiness for the build. The Windows Schannel minimum-build documentation and Insider build labeling were inconsistent in the source investigation.
2. **Scope of cryptography:** A hybrid `X25519MLKEM768` key exchange does not prove quantum-resistant authentication. Certificate signature algorithms, entropy provenance, private key protection, endpoint side channels and downgrade resistance were not comprehensively assessed.
3. **Application stacks:** Browsers can use their own TLS engines. A Schannel setting is not a universal endpoint-level policy for all TLS traffic.
4. **Version drift:** Edge `158.0.4370.33` → `158.0.4370.45` and Firefox `160.0.1` → `161.0` changed between supplemental State A and State B. Chrome version remained recorded as `158.0.8127.38`. Static baseline-version metadata is not independent runtime attestation.
5. **S2 terminology:** The S2 server was **hybrid-only**, not ML-KEM-only; X25519 is still part of the standardized hybrid.
6. **TLS alerts:** Alert 40 is `handshake_failure`; the lack of a mutually acceptable key share is the protocol-consistent interpretation, not something proved by the alert value alone.
7. **Capture granularity:** Browsers may establish multiple TCP/TLS streams per capture, so capture counts and handshake counts must not be conflated.
8. **Validation boundary:** The 60/60 preliminary packet-level audit did not prove application-layer integrity cryptographically, and CI does not reanalyze PCAPNGs. The private packet archive must be available for full independent replication.
9. **Supplementary data:** Twelve post-freeze State A browser runs are labeled separately and cannot be claimed to have been part of the preregistered 48-run design.
10. **Privacy:** Private packet captures, internal addresses, keys, raw RDP logs and VM images are intentionally excluded from the public release.
