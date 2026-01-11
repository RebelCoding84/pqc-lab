from __future__ import annotations

from pqc_lab import __version__
from pqc_lab.energy import run_energy_scenario_monte_carlo
from pqc_lab.finance import run_finance_monte_carlo
from pqc_lab.pqc_adapter import run_pqc_roundtrip
from pqc_lab.quantum import run_quantum_smoke


def test_package_version() -> None:
    assert __version__


def test_quantum_demo_runs() -> None:
    counts = run_quantum_smoke(shots=128)
    assert isinstance(counts, dict)
    assert counts


def test_finance_demo_runs() -> None:
    result = run_finance_monte_carlo(n_paths=2000)
    assert result["price"] > 0.0


def test_energy_demo_runs() -> None:
    result = run_energy_scenario_monte_carlo(n=500)
    assert result["mean_price"] > 0.0


def test_pqc_demo_optional() -> None:
    result = run_pqc_roundtrip()
    assert result.status in {"ok", "skipped"}
    if result.status == "skipped":
        assert "PQC provider not installed" in result.detail
