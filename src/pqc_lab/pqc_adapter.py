"""PQC adapter with optional provider detection.

The adapter attempts to use an installed PQC provider and falls back to a
non-failing message when no provider is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PqcResult:
    status: str
    provider: Optional[str]
    detail: str


def _try_pqcrypto_kem() -> Optional[PqcResult]:
    try:
        from pqcrypto.kem import kyber512
    except Exception:
        return None

    public_key, secret_key = kyber512.generate_keypair()
    ciphertext, shared_secret_enc = kyber512.encrypt(public_key)
    shared_secret_dec = kyber512.decrypt(ciphertext, secret_key)

    if shared_secret_enc != shared_secret_dec:
        raise RuntimeError("PQC KEM roundtrip failed")

    return PqcResult(status="ok", provider="pqcrypto.kyber512", detail="KEM roundtrip succeeded")


def run_pqc_roundtrip() -> PqcResult:
    """Run a PQC roundtrip using an optional provider.

    Returns a PqcResult with status "ok" or "skipped" when no provider is found.
    """

    result = _try_pqcrypto_kem()
    if result is not None:
        return result

    return PqcResult(
        status="skipped",
        provider=None,
        detail="PQC provider not installed; run `pixi add <provider>` or enable profile",
    )
