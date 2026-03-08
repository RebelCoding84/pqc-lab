#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

export OQS_INSTALL_PATH=/home/rebel/_oqs
if [ -d "$OQS_INSTALL_PATH/lib64" ]; then
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib64:${LD_LIBRARY_PATH:-}"
else
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib:${LD_LIBRARY_PATH:-}"
fi

cd "$REPO_ROOT"

echo "OQS_INSTALL_PATH=$OQS_INSTALL_PATH"
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

echo "python -c \"import oqs; print(oqs.__file__)\""
if ! python -c "import oqs; print(oqs.__file__)"; then
  echo "WARN: oqs module path probe failed."
fi

echo "python -c \"import oqs; print([m for m in oqs.get_enabled_sig_mechanisms() if 'ML-DSA' in m])\""
if ! python -c "import oqs; print([m for m in oqs.get_enabled_sig_mechanisms() if 'ML-DSA' in m])"; then
  echo "WARN: ML-DSA mechanism probe failed."
fi

python - <<'PY'
from __future__ import annotations

import sys


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


try:
    import oqs  # type: ignore
except ModuleNotFoundError as exc:
    if getattr(exc, "name", None) == "oqs":
        print(
            "ERROR: missing module 'oqs'. "
            "Run `pixi run --environment pqc-real bootstrap-oqs` first.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(f"ERROR: failed to import oqs: {exc}", file=sys.stderr)
    raise SystemExit(1)
except Exception as exc:
    print(f"ERROR: failed to import oqs: {exc}", file=sys.stderr)
    raise SystemExit(1)


def _load_sig_mechanisms() -> list[str]:
    for attr in (
        "get_enabled_sig_mechanisms",
        "get_sig_mechanisms",
        "get_supported_sig_mechanisms",
    ):
        getter = getattr(oqs, attr, None)
        if not callable(getter):
            continue
        try:
            values = getter()
        except Exception:
            continue
        if isinstance(values, (list, tuple, set)):
            return sorted(str(item) for item in values if isinstance(item, str))
    return []


mechanisms = _load_sig_mechanisms()
if not mechanisms:
    print("ERROR: oqs import succeeded but no signature mechanisms were discovered.", file=sys.stderr)
    raise SystemExit(1)

print(f"python executable: {sys.executable}")
print(f"oqs module path: {getattr(oqs, '__file__', '<unknown>')}")
print("oqs import: OK")
print("Enabled stateless signature mechanisms:")
for mechanism in mechanisms:
    print(f" - {mechanism}")

mldsa = [name for name in mechanisms if _normalize(name).startswith("mldsa")]
print("Filtered ML-DSA mechanisms:")
if mldsa:
    for mechanism in sorted(mldsa):
        print(f" - {mechanism}")
else:
    print(" - <none>")

if not mldsa:
    print("ERROR: no ML-DSA signature mechanism is available in this oqs runtime.", file=sys.stderr)
    raise SystemExit(1)
PY
