from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from capacity import signature_pool, verify_runner, verify_providers


def _write_profile(
    path: Path,
    *,
    provider: str,
    pool_path: Path,
    output_dir: Path,
    concurrency: int,
) -> None:
    payload = {
        "schema_version": 1,
        "benchmark_name": "test_verify_capacity",
        "operation": "verify",
        "provider": provider,
        "algorithm": "ML-DSA",
        "pool_path": str(pool_path),
        "concurrency": concurrency,
        "warmup_s": 0.01,
        "duration_s": 0.05,
        "repeats": 1,
        "output_dir": str(output_dir),
        "notes": {"phase": "phase1", "purpose": "test"},
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")


def _make_mock_pool(path: Path, size: int = 64) -> None:
    signature_pool.generate_pool(
        provider_name="mock_verify",
        algorithm="ML-DSA",
        pool_size=size,
        out_path=path,
    )


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        if not value:
            return []
        return [_shape(value[0])]
    return type(value).__name__


def test_profile_schema_validation_rejects_unknown_field(tmp_path: Path) -> None:
    bad_profile = tmp_path / "bad_profile.yaml"
    bad_payload = {
        "schema_version": 1,
        "benchmark_name": "bad",
        "operation": "verify",
        "provider": "mock_verify",
        "algorithm": "ML-DSA",
        "pool_path": str(tmp_path / "pool.jsonl"),
        "concurrency": 1,
        "warmup_s": 0,
        "duration_s": 1,
        "repeats": 1,
        "output_dir": str(tmp_path / "out"),
        "unknown_field": True,
    }
    bad_profile.write_text(yaml.safe_dump(bad_payload, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown fields"):
        verify_runner.load_verify_profile(bad_profile)


def test_mock_report_shape_is_deterministic(tmp_path: Path) -> None:
    pool_path = tmp_path / "mock_pool.jsonl"
    _make_mock_pool(pool_path, size=32)

    profile_path = tmp_path / "profile.yaml"
    _write_profile(
        profile_path,
        provider="mock_verify",
        pool_path=pool_path,
        output_dir=tmp_path / "reports",
        concurrency=2,
    )
    profile = verify_runner.load_verify_profile(profile_path)

    report_one = verify_runner.run_verify_benchmark(profile, profile_path=profile_path)
    report_two = verify_runner.run_verify_benchmark(profile, profile_path=profile_path)

    assert _shape(report_one) == _shape(report_two)


@pytest.mark.parametrize(
    "profile_relpath",
    [
        "profiles/verify_capacity/mock_verify_c1.yaml",
        "profiles/verify_capacity/mock_verify_c8.yaml",
    ],
)
def test_mock_profiles_complete_successfully(profile_relpath: str, tmp_path: Path) -> None:
    fixture_pool = REPO_ROOT / "fixtures/signatures/mock_verify_pool_256.jsonl"
    assert fixture_pool.exists()

    base_profile = yaml.safe_load((REPO_ROOT / profile_relpath).read_text(encoding="utf-8"))
    assert isinstance(base_profile, dict)
    base_profile["pool_path"] = str(fixture_pool)
    base_profile["output_dir"] = str(tmp_path / "reports")

    profile_path = tmp_path / Path(profile_relpath).name
    profile_path.write_text(yaml.safe_dump(base_profile, sort_keys=True), encoding="utf-8")

    exit_code = verify_runner.main(["--profile", str(profile_path)])
    assert exit_code == 0

    parsed = verify_runner.load_verify_profile(profile_path)
    output_path = verify_runner._build_output_path(parsed)
    assert output_path.exists()

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["operation"] == "verify"
    assert report["provider"] == "mock_verify"
    assert report["algorithm"] == "ML-DSA"
    assert report["pool_size"] == 256


def test_pool_generator_excludes_private_key_material(tmp_path: Path) -> None:
    pool_path = tmp_path / "pool.jsonl"
    signature_pool.generate_pool(
        provider_name="mock_verify",
        algorithm="ML-DSA",
        pool_size=10,
        out_path=pool_path,
    )

    raw = pool_path.read_text(encoding="utf-8").lower()
    assert "private_key" not in raw
    assert "secret_key" not in raw

    lines = [line for line in pool_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    for index, raw_line in enumerate(lines):
        obj = json.loads(raw_line)
        if index == 0:
            assert obj["record_type"] == "metadata"
            continue
        assert set(obj.keys()) == {"public_key", "message", "signature"}


def test_runner_fails_when_real_provider_unavailable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    statuses = {status.provider: status for status in verify_providers.list_provider_statuses()}
    if statuses["real_mldsa"].available:
        pytest.skip("real_mldsa provider is available in this runtime")

    pool_path = tmp_path / "pool.jsonl"
    _make_mock_pool(pool_path, size=16)

    profile_path = tmp_path / "real_profile.yaml"
    _write_profile(
        profile_path,
        provider="real_mldsa",
        pool_path=pool_path,
        output_dir=tmp_path / "reports",
        concurrency=1,
    )
    exit_code = verify_runner.main(["--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unavailable" in captured.err.lower()

