from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.capacity import harness


def test_detect_git_commit_prefers_env_and_falls_back_to_unknown(monkeypatch) -> None:
    monkeypatch.setenv("GIT_COMMIT", "abc123")
    assert harness._detect_git_commit() == "abc123"

    monkeypatch.delenv("GIT_COMMIT", raising=False)
    assert harness._detect_git_commit() == "unknown"


def test_detect_in_container_true_in_ci(monkeypatch) -> None:
    monkeypatch.setenv("CI", "true")
    assert harness._detect_in_container() is True


def test_build_environment_contains_required_audit_fields(monkeypatch) -> None:
    monkeypatch.setenv("GIT_COMMIT", "commit-sha")
    env = harness._build_environment()

    assert env["git_commit"] == "commit-sha"
    assert isinstance(env["in_container"], bool)
    for key in (
        "platform",
        "python_version",
        "os_release",
        "kernel_release",
        "machine",
        "timestamp_utc",
    ):
        assert key in env
