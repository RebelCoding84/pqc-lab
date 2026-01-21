from __future__ import annotations

from pathlib import Path

import pytest

from crypto_agility.runner import run_profile
from crypto_agility.schema import load_profile


def _load_profile_from_repo(rel_path: str):
    return load_profile(Path(__file__).resolve().parents[1] / rel_path)


def _strip_elapsed(report: dict) -> dict:
    sanitized = dict(report)
    sanitized.pop("elapsed_ms", None)
    return sanitized


def test_deterministic_report_matches() -> None:
    profile = _load_profile_from_repo("profiles/mock_ecdh.yaml")
    report_one = run_profile(profile)
    report_two = run_profile(profile)

    assert report_one["elapsed_ms"] >= 0
    assert report_two["elapsed_ms"] >= 0
    assert _strip_elapsed(report_one) == _strip_elapsed(report_two)


@pytest.mark.parametrize(
    "payload",
    [
        """
        name: bad
        key_exchange:
          algorithm: mock_ecdh
          iterations: 1
          seed_mode: deterministic
          seed: 1
          failure_injection: false
        extra: true
        """,
        """
        name: bad
        key_exchange:
          algorithm: mock_ecdh
          iterations: 10001
          seed_mode: deterministic
          seed: 1
          failure_injection: false
        """,
        """
        name: bad
        key_exchange:
          algorithm: mock_ecdh
          iterations: 1
          seed_mode: deterministic
          seed: 4294967296
          failure_injection: false
        """,
        """
        name: bad
        key_exchange:
          algorithm: mock_ecdh
          iterations: 1
          seed_mode: deterministic
          seed: 1
          failure_injection: false
          unknown_field: 7
        """,
    ],
)
def test_schema_validation_rejects_invalid(payload: str, tmp_path: Path) -> None:
    profile_path = tmp_path / "bad.yaml"
    profile_path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError):
        load_profile(profile_path)


@pytest.mark.parametrize("profile_path", ["profiles/mock_ecdh.yaml", "profiles/mock_pqc_kem.yaml"])
def test_success_counts_for_profiles(profile_path: str) -> None:
    profile = _load_profile_from_repo(profile_path)
    report = run_profile(profile)

    assert report["success_count"] == report["iterations"]
    assert report["failure_count"] == 0
