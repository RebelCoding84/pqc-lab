from __future__ import annotations

"""NON-PRODUCTION mock key-exchange runner for crypto-agility orchestration."""

import hashlib
import hmac
import random
import time
from typing import Any

from .schema import Profile

HYBRID_SALT = b"pqc-lab-hybrid"
HYBRID_INFO = b"crypto-agility-hybrid"


def run_profile(profile: Profile) -> dict[str, Any]:
    start = time.perf_counter()
    success_count = 0
    failure_count = 0
    rng = random.Random(profile.key_exchange.seed)

    if profile.provider == "liboqs":
        from .backend import run_kem_exchange

        if profile.key_exchange.hybrid is not None:
            component_lengths: dict[str, int] = {}
            algorithms = list(profile.key_exchange.hybrid.algorithms)
            for index in range(profile.key_exchange.iterations):
                seed_material = _derive_iteration_seed(profile.key_exchange.seed, index)
                try:
                    ss1, len1 = _run_liboqs_component(run_kem_exchange, algorithms[0], seed_material)
                    ss2, len2 = _run_liboqs_component(run_kem_exchange, algorithms[1], seed_material)
                    component_lengths.setdefault(algorithms[0], len1)
                    component_lengths.setdefault(algorithms[1], len2)
                    _ = _hkdf_sha256(
                        ss1 + ss2,
                        salt=HYBRID_SALT,
                        info=HYBRID_INFO,
                        length=profile.key_exchange.hybrid.output_len,
                    )
                    success_count += 1
                except Exception:
                    failure_count += 1
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "profile_name": profile.name,
                "mode": "hybrid",
                "hybrid_algorithms": algorithms,
                "component_shared_secret_lengths": component_lengths,
                "derived_shared_secret_length": profile.key_exchange.hybrid.output_len,
                "kdf": profile.key_exchange.hybrid.kdf,
                "iterations": profile.key_exchange.iterations,
                "deterministic": profile.key_exchange.seed_mode == "deterministic",
                "success_count": success_count,
                "failure_count": failure_count,
                "elapsed_ms": elapsed_ms,
                "metadata": dict(profile.metadata),
                "provider": "liboqs",
            }

        backend_result = run_kem_exchange(
            {
                "provider": "liboqs",
                "algorithm": profile.key_exchange.algorithm,
                "iterations": profile.key_exchange.iterations,
            }
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {
            "profile_name": profile.name,
            "algorithm": profile.key_exchange.algorithm,
            "iterations": profile.key_exchange.iterations,
            "deterministic": profile.key_exchange.seed_mode == "deterministic",
            "success_count": profile.key_exchange.iterations,
            "failure_count": 0,
            "elapsed_ms": elapsed_ms,
            "metadata": dict(profile.metadata),
            "provider": "liboqs",
            "mechanism": backend_result["mechanism"],
            "shared_secret_length": backend_result["shared_secret_length"],
        }

    for index in range(profile.key_exchange.iterations):
        _derive_secret(profile.key_exchange.seed, index, profile.key_exchange.algorithm)
        if profile.key_exchange.failure_injection and rng.random() < 0.1:
            failure_count += 1
        else:
            success_count += 1

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return {
        "profile_name": profile.name,
        "algorithm": profile.key_exchange.algorithm,
        "iterations": profile.key_exchange.iterations,
        "deterministic": profile.key_exchange.seed_mode == "deterministic",
        "success_count": success_count,
        "failure_count": failure_count,
        "elapsed_ms": elapsed_ms,
        "metadata": dict(profile.metadata),
    }


def _derive_secret(seed: int, index: int, label: str) -> bytes:
    digest = hashlib.sha256()
    digest.update(f"{seed}:{index}:{label}".encode("utf-8"))
    return digest.digest()


def _derive_iteration_seed(seed: int, index: int) -> bytes:
    digest = hashlib.sha256()
    digest.update(f"{seed}:{index}".encode("utf-8"))
    return digest.digest()


def _run_liboqs_component(run_kem_exchange, algorithm: str, seed_material: bytes) -> tuple[bytes, int]:
    backend_result = run_kem_exchange(
        {
            "provider": "liboqs",
            "algorithm": algorithm,
            "iterations": 1,
            "seed_material": seed_material,
            "return_shared_secret": True,
        }
    )
    shared_secret = backend_result.get("shared_secret")
    if not isinstance(shared_secret, (bytes, bytearray)):
        raise ValueError("liboqs backend did not return a shared secret.")
    return bytes(shared_secret), int(backend_result["shared_secret_length"])


def _hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    hash_len = hashlib.sha256().digest_size
    if not salt:
        salt = b"\x00" * hash_len
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    t = b""
    counter = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        okm += t
        counter += 1
    return okm[:length]
