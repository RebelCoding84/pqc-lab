"""Provider-based KEM exchange helpers (opt-in)."""

from __future__ import annotations

def run_kem_exchange(profile: dict) -> dict:
    """Run a KEM exchange using the requested provider."""
    provider = profile.get("provider")
    if provider == "mock":
        return run_mock_exchange(profile)
    if provider == "liboqs":
        return run_liboqs_exchange(profile)
    raise ValueError(f"Unknown provider: {provider}")


def run_mock_exchange(profile: dict) -> dict:
    """Deterministic mock KEM exchange."""
    return {
        "status": "success",
        "provider": "mock",
        "mechanism": "MOCK-KEM",
        "shared_secret_length": 32,
        "iterations": profile.get("iterations", 1),
    }


def run_liboqs_exchange(profile: dict) -> dict:
    """Run a KEM exchange via liboqs-python."""
    import oqs

    algorithm = profile.get("algorithm")
    if not algorithm:
        raise ValueError("Missing algorithm in profile")
    kem = oqs.KeyEncapsulation(algorithm)
    public_key = kem.generate_keypair()
    ciphertext, shared_secret_bob = kem.encap_secret(public_key)
    shared_secret_alice = kem.decap_secret(ciphertext)

    if shared_secret_alice != shared_secret_bob:
        raise ValueError("Shared secret mismatch")

    mechanism = getattr(kem, "details", {}).get("name", algorithm)
    return {
        "status": "success",
        "provider": "liboqs",
        "mechanism": mechanism,
        "shared_secret_length": len(shared_secret_alice),
        "iterations": profile.get("iterations", 1),
    }
