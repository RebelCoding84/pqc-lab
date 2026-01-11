import numpy as np


def run_energy_scenario_monte_carlo(seed: int = 42, n: int = 10_000):
    rng = np.random.default_rng(seed)
    prices = rng.normal(loc=50.0, scale=10.0, size=n)
    total_cost = prices.sum()
    return {
        "mean_price": float(prices.mean()),
        "total_cost": float(total_cost),
        "samples": n,
    }
