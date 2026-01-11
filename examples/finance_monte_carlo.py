"""Simple Black-Scholes Monte Carlo for a European call option."""

from __future__ import annotations

from pqc_lab.finance import run_finance_monte_carlo


def main() -> None:
    result = run_finance_monte_carlo()
    print("Black-Scholes Monte Carlo")
    print("Parameters:", result)


if __name__ == "__main__":
    main()
