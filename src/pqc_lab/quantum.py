"""Quantum demo helpers."""

from __future__ import annotations

from typing import Dict

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def run_quantum_smoke(shots: int = 256) -> Dict[str, int]:
    """Build and run a tiny Bell circuit on the Aer CPU backend."""

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    backend = AerSimulator()
    compiled = transpile(circuit, backend)
    result = backend.run(compiled, shots=shots).result()
    counts = result.get_counts()

    return counts
