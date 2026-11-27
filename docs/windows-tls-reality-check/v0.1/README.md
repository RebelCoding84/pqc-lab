# Windows TLS Reality Check v0.1 — measurement report

**Status:** Draft research release; the original PCAPNG evidence remains private.  
**Protocol:** v0.1 FROZEN, drafted 2026-10-20 and registered 2026-11-16.  
**Measurements:** November 2026.  
**Source repository (offline):** `win-tls-check`, commit `7e20117f3b80564b533204a360febd798dacd763`.

## Research question

Does enabling `x25519_mlkem768` in Windows Schannel change negotiated TLS 1.3 key exchange in Schannel-based clients, and do Edge, Chrome and Firefox behave differently?

## Environment and test design

- Windows 11 Pro Insider Preview, build `26320.9876` (observed in the laboratory; functionality is **not** a vendor support guarantee).
- Fedora host, OpenSSL `3.5.9` and TShark `4.6.9`.
- Clients: Windows curl `8.22.0` (Schannel), Windows PowerShell `5.1`, PowerShell `7.7.0`, Edge, Chrome and Firefox.
- **State A:** hybrid group not active in Schannel. **State B:** `x25519_mlkem768` enabled at position 0 after controlled change and reboot.
- **S1:** OpenSSL TLS 1.3 accepts `X25519MLKEM768/X25519`; **S2:** accepts only `X25519MLKEM768` (a *hybrid-only*, not ML-KEM-only, server).
- Original preregistered matrix: 48 runs; 12 supplementary State A browser runs after browser updates; the supplemental data are **not** retroactive replacements for the original protocol.

## Measurements and results

Each row of [results.csv](results.csv) represents one selected capture and its operator-reported result. The 60 selected measurements passed local metadata and SHA-256 checks and an offline TShark-based *preliminary* packet-level audit. The data file includes SHA-256 digests that identify the privately retained captures; the captures are **not** distributed here.

| Cohort / state / profile | Runs | Result |
|---|---:|---|
| Primary A / S1 | 18 | 9 classic X25519 (`29`); 9 hybrid (`4588`) |
| Primary A / S2 | 6 | 3 Schannel `TLS_ERROR`; 3 browser hybrid (`4588`) |
| Primary B / S1 | 18 | 18 hybrid (`4588`) |
| Primary B / S2 | 6 | 6 hybrid (`4588`) |
| Supplemental A / S1 | 9 | 9 browser hybrid (`4588`) |
| Supplemental A / S2 | 3 | 3 browser hybrid (`4588`) |
| **Total** | **60** | **57 operator-reported HTTP 200; 3 expected TLS errors** |

- Among the **accepted** captures, 48 selected `X25519MLKEM768` (IANA `4588`), 9 selected X25519 (`29`), and 3 had no final ServerHello.
- The three State A / S2 Schannel failure captures each contain one ClientHello, no final ServerHello, and TLS alert **40 (`handshake_failure`)**. Group incompatibility is consistent with their ClientHello key shares and the S2 profile; the alert alone does not establish root cause.
- No HelloRetryRequest was observed in the 60 selected captures. This does not exclude HRR elsewhere, including preflight tests.
- Browser records already showed hybrid negotiation in State A, indicating that the observed browser behavior was not dependent on Schannel's active group list in the same way as curl and PowerShell in this environment.
- Several browser captures contain more than one TCP stream; **a capture is not a single handshake**. Counts are recorded separately.

## Browser-version confounding

The supplemental State A and State B versions were recorded as follows:

| Browser | Supplemental State A | State B |
|---|---|---|
| Edge | `158.0.4370.33` | `158.0.4370.45` |
| Chrome | `158.0.8127.38` | `158.0.8127.38` |
| Firefox | `160.0.1` | `161.0` |

Edge and Firefox changed versions; causal attribution of their A/B differences solely to the Schannel configuration would be invalid. The frozen runner's `baseline_expected_client_version` is a static baseline, **not** independent runtime version attestation.

## Evidence, reproducibility and limitations

- **Public validation:** `python3 scripts/validate_windows_tls_dataset.py` checks the released CSV schema, expected selected-run matrix, deduplication, group observations, operator outcomes, and digest syntax; the dedicated GitHub Actions workflow runs these checks and negative tests.
- **Private evidence:** Original PCAPNGs, contemporaneous metadata, TShark logs, source checkpoints and local backup remain in a separate private archive. Local integrity audit: **67/67** available captures passed recorded SHA-256 checks; 60 selected captures passed the preliminary packet-level audit.
- **Unverified externally:** GitHub Actions cannot independently re-extract TLS fields or verify private PCAPNG bytes without access to those files. It verifies *the published derivative dataset*, not the Windows/Schannel experiment itself.
- Only negotiated key-exchange groups were evaluated. This is **not** evidence that certificate authentication, entropy generation, implementation security, or all Windows traffic is post-quantum secure. Do not treat the Insider build as a supported production configuration.

See [methodology](methodology.md), [limitations](limitations.md) and the [recorded amendments](amendments.md).
