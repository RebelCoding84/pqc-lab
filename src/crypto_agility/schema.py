from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

ALLOWED_ALGORITHMS = {"mock_ecdh", "mock_pqc_kem"}
MAX_SEED = 2**32 - 1


@dataclass(frozen=True)
class KeyExchangeConfig:
    algorithm: str
    iterations: int
    seed_mode: str
    seed: int
    failure_injection: bool


@dataclass(frozen=True)
class Profile:
    name: str
    provider: str | None
    key_exchange: KeyExchangeConfig
    metadata: dict[str, str | int | bool]


def load_profile(path: str | Path) -> Profile:
    data = _load_yaml(path)
    return _parse_profile(data)


def _load_yaml(path: str | Path) -> Mapping[str, Any]:
    raw = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, Mapping):
        raise ValueError("Profile YAML must be a mapping at the top level.")
    return data


def _parse_profile(data: Mapping[str, Any]) -> Profile:
    _require_keys(
        data,
        {"name", "key_exchange", "metadata", "provider"},
        {"name", "key_exchange"},
        "profile",
    )
    name = data["name"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Profile name must be a non-empty string.")

    provider = data.get("provider")
    if provider is not None:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider must be a non-empty string if set.")
        if provider != "liboqs":
            raise ValueError("provider must be 'liboqs' if set.")

    key_exchange_raw = data["key_exchange"]
    if not isinstance(key_exchange_raw, Mapping):
        raise ValueError("key_exchange must be a mapping.")
    key_exchange = _parse_key_exchange(key_exchange_raw, provider)

    metadata_raw = data.get("metadata", {})
    metadata = _parse_metadata(metadata_raw)
    return Profile(name=name, provider=provider, key_exchange=key_exchange, metadata=metadata)


def _parse_key_exchange(data: Mapping[str, Any], provider: str | None) -> KeyExchangeConfig:
    _require_keys(
        data,
        {"algorithm", "iterations", "seed_mode", "seed", "failure_injection"},
        {"algorithm", "iterations", "seed_mode", "seed", "failure_injection"},
        "key_exchange",
    )
    algorithm = data["algorithm"]
    if provider == "liboqs":
        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("algorithm must be a non-empty string.")
    else:
        if algorithm not in ALLOWED_ALGORITHMS:
            raise ValueError(f"algorithm must be one of {sorted(ALLOWED_ALGORITHMS)}.")

    iterations = data["iterations"]
    if not isinstance(iterations, int) or not (1 <= iterations <= 10_000):
        raise ValueError("iterations must be an int between 1 and 10000.")

    seed_mode = data["seed_mode"]
    if seed_mode != "deterministic":
        raise ValueError("seed_mode must be 'deterministic'.")

    seed = data["seed"]
    if not isinstance(seed, int) or not (0 <= seed <= MAX_SEED):
        raise ValueError(f"seed must be an int between 0 and {MAX_SEED}.")

    failure_injection = data["failure_injection"]
    if not isinstance(failure_injection, bool):
        raise ValueError("failure_injection must be a boolean.")

    return KeyExchangeConfig(
        algorithm=algorithm,
        iterations=iterations,
        seed_mode=seed_mode,
        seed=seed,
        failure_injection=failure_injection,
    )


def _parse_metadata(metadata: Any) -> dict[str, str | int | bool]:
    if metadata is None:
        return {}
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping if provided.")
    sanitized: dict[str, str | int | bool] = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ValueError("metadata keys must be strings.")
        if not isinstance(value, (str, int, bool)):
            raise ValueError("metadata values must be str, int, or bool.")
        sanitized[key] = value
    return sanitized


def _require_keys(
    data: Mapping[str, Any],
    allowed: set[str],
    required: set[str],
    context: str,
) -> None:
    extra = set(data.keys()) - allowed
    if extra:
        raise ValueError(f"Unknown fields in {context}: {sorted(extra)}.")
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Missing required fields in {context}: {sorted(missing)}.")
