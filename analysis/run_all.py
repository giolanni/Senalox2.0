"""Esegue gli esperimenti iniziali senza avviare alcuna interfaccia grafica."""
from analysis.experiments.parity.run import main as run_parity
from analysis.laboratory.trigger_patterns.single_number_window import run as run_trigger


def main() -> None:
    run_parity()
    for dataset in ("OVERALL", "NEW_MODE"):
        run_trigger(dataset, window_size=9, pool_size=13, simulations=50, seed=20260805)


if __name__ == "__main__":
    main()
