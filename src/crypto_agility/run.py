from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .runner import run_profile
from .schema import load_profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Crypto-agility test harness (NON-PRODUCTION mocks)."
    )
    parser.add_argument("--profile", required=True, help="Path to the YAML profile.")
    parser.add_argument("--out", help="Optional output path for the JSON report.")
    args = parser.parse_args(argv)

    profile = load_profile(args.profile)
    report = run_profile(profile)
    payload = _to_json(report)
    print(payload)

    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    return 0


def _to_json(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
