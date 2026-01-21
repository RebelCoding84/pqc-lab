from __future__ import annotations

"""NON-PRODUCTION mock key-exchange runner for crypto-agility orchestration."""

import hashlib
import random
import time
from typing import Any

from .schema import Profile


def run_profile(profile: Profile) -> dict[str, Any]:
    start = time.perf_counter()
    success_count = 0
    failure_count = 0
    rng = random.Random(profile.key_exchange.seed)

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
