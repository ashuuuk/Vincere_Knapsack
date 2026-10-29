
"""Run the PS-O3 QAOA experiment and save reproducible benchmark outputs."""

import json
from pathlib import Path

import pandas as pd
from qiskit_aer import AerSimulator

from src.problem import classical_bruteforce
from src.processors import load_processor, build_noise_model
from src.routing import (
    build_qaoa_circuit,
    optimize_qaoa_grid,
    transpile_for_processor,
)
from src.metrics import circuit_metrics, summarize_counts
from src.visualization import (
    plot_coupling,
    plot_comparison,
    plot_o3_landscape,
)

ROOT = Path(__file__).resolve().parent


def main():
    results_dir = ROOT / "results"
    tables_dir = results_dir / "tables"
    figures_dir = results_dir / "figures"
    data_dir = ROOT / "data" / "processed"

    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    values = [10, 4, 7, 5, 8]
    weights = [5, 3, 4, 2, 6]
    capacity = 15

    # Compute the exact classical reference and optimize the p=1 QAOA grid.
    classical_optimum, qubo_ground_states, qubo_ground_energy = (
        classical_bruteforce()
    )
    params = optimize_qaoa_grid()

    logical = build_qaoa_circuit(params["gamma"], params["beta"])
    logical_measured = build_qaoa_circuit(
        params["gamma"], params["beta"], measured=True
    )

    summary = {
        "problem_statement": "PS-O3: Combinatorial 0-1 Knapsack Problem",
        "instance": {
            "values": values,
            "weights": weights,
            "capacity": capacity,
        },
        "classical_constrained_optimum": classical_optimum,
        "qubo_ground_states": qubo_ground_states,
        "qubo_ground_energy": qubo_ground_energy,
        "qaoa_parameters": params,
        "note": (
            "Synthetic noise only; results are simulation results, "
            "not real hardware measurements."
        ),
        "processor_A_status": (
            "Not executable for O3: the circuit uses 9 qubits, "
            "while Processor A has 5 physical qubits."
        ),
    }

    (data_dir / "classical_reference.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    metric_rows = []
    result_rows = []

    # Processor A cannot execute this 9-qubit O3 circuit.
    for name in ["processor_B", "processor_D"]:
        config = load_processor(name)

        plot_coupling(
            {
                key: value
                for key, value in config.items()
                if key != "coupling"
            },
            figures_dir / f"{name}_coupling.png",
        )

        compiled = transpile_for_processor(logical_measured, config)
        metrics = circuit_metrics(logical, compiled)

        simulator = AerSimulator(
            noise_model=build_noise_model(config)
        )
        counts = (
            simulator.run(
                compiled,
                shots=config["shots"],
                seed_simulator=42,
            )
            .result()
            .get_counts()
        )

        sampled = summarize_counts(counts)

        metric_rows.append({
            "processor": config["name"],
            **metrics,
        })

        result_rows.append({
            "processor": config["name"],
            **{
                key: value
                for key, value in sampled.items()
                if key != "counts"
            },
        })

        pd.DataFrame(sampled["counts"]).to_csv(
            tables_dir / f"{name}_counts.csv",
            index=False,
        )

    metrics_df = pd.DataFrame(metric_rows)
    results_df = pd.DataFrame(result_rows)

    metrics_df.to_csv(
        tables_dir / "processor_metrics.csv",
        index=False,
    )
    results_df.to_csv(
        tables_dir / "sampled_results.csv",
        index=False,
    )

    plot_comparison(
        metrics_df,
        figures_dir / "processor_comparison.png",
    )

    plot_o3_landscape(
        values=values,
        weights=weights,
        capacity=capacity,
        output_path=figures_dir / "o3_solution_landscape.png",
    )

    summary["circuit_metrics"] = metric_rows
    summary["noisy_sampled_results"] = result_rows

    (tables_dir / "benchmark_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("Classical constrained optimum:", classical_optimum)
    print("QAOA parameters:", params)

    print("\nCircuit metrics:\n", metrics_df.to_string(index=False))
    print("\nNoisy sampled results:\n", results_df.to_string(index=False))

    print("\nSaved CSV, JSON and PNG outputs under results/.")


if __name__ == "__main__":
    main()
