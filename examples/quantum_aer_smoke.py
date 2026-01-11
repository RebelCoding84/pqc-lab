"""CPU-only Qiskit Aer smoke test."""

from __future__ import annotations

import sys

import qiskit

from pqc_lab.quantum import run_quantum_smoke


def main() -> None:
    print(f"Python {sys.version.split()[0]} | Qiskit {qiskit.__version__}")
    counts = run_quantum_smoke()
    print("Counts:", counts)


if __name__ == "__main__":
    main()
