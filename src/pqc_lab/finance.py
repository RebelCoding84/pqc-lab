"""Finance Monte Carlo routines."""

from __future__ import annotations

from typing import Dict

import numpy as np


def run_finance_monte_carlo(
    s0: float = 100.0,
    strike: float = 100.0,
    rate: float = 0.05,
    volatility: float = 0.2,
    maturity: float = 1.0,
    n_paths: int = 10000,
    seed: int = 42,
) -> Dict[str, float]:
    """Return a Monte Carlo estimate for a European call price."""

    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n_paths)
    st = s0 * np.exp((rate - 0.5 * volatility ** 2) * maturity + volatility * np.sqrt(maturity) * z)
    payoff = np.maximum(st - strike, 0.0)
    price = np.exp(-rate * maturity) * np.mean(payoff)

    return {
        "price": float(price),
        "s0": s0,
        "strike": strike,
        "rate": rate,
        "volatility": volatility,
        "maturity": maturity,
        "paths": float(n_paths),
    }
