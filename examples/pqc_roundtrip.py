"""PQC roundtrip demo with optional provider support."""

from __future__ import annotations

import sys

from pqc_lab.pqc_adapter import run_pqc_roundtrip


def main() -> int:
    result = run_pqc_roundtrip()
    if result.status == "skipped":
        print(result.detail)
        return 0

    print(f"PQC provider: {result.provider}")
    print(result.detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
