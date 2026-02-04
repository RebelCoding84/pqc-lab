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
    seed_material = profile.get("seed_material")
    if seed_material is not None:
        _maybe_seed_oqs(oqs, seed_material)

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
    response = {
        "status": "success",
        "provider": "liboqs",
        "mechanism": mechanism,
        "shared_secret_length": len(shared_secret_alice),
        "iterations": profile.get("iterations", 1),
    }
    if profile.get("return_shared_secret"):
        response["shared_secret"] = shared_secret_alice
    return response


def _maybe_seed_oqs(oqs_module, seed_material: bytes) -> None:
    rand = getattr(oqs_module, "rand", None)
    if rand is None:
        return
    init_fn = getattr(rand, "randombytes_init", None)
    if init_fn is None:
        return
    try:
        init_fn(seed_material, b"pqc-lab-hybrid")
    except TypeError:
        try:
            init_fn(seed_material)
        except Exception:
            return
