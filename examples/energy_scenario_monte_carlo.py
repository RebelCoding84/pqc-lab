"""Energy scenario runner that delegates to library logic."""

from pqc_lab.energy import run_energy_scenario_monte_carlo


def main() -> None:
    result = run_energy_scenario_monte_carlo()
    print("Energy scenario result:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
