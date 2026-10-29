
"""Run reproducible PS-O3 QAOA experiments and save benchmark outputs."""

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit_aer import AerSimulator

from src.problem import (
    VALUES,
    WEIGHTS,
    CAPACITY,
    N_ITEMS,
    classical_bruteforce,
    evaluate_bits,
)
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
SHOTS = 4096
SEED = 42

RESULT_COLUMNS = [
    "problem_id",
    "processor",
    "condition",
    "executable",
    "logical_qubits",
    "physical_qubits",
    "logical_cx",
    "cx",
    "depth",
    "two_q_depth",
    "swaps",
    "cx_overhead",
    "shots",
    "quality_metric",
    "quality_value",
    "p_opt",
    "classical_optimum",
    "random_baseline",
]


def exact_random_baseline(optimum_value):
    """Enumerate all equally likely item subsets for an exact baseline."""
    feasible_count = 0
    optimal_count = 0
    subset_count = 1 << N_ITEMS

    for mask in range(subset_count):
        bits = [(mask >> i) & 1 for i in range(N_ITEMS)]

        result = evaluate_bits(
            bits,
            values=VALUES,
            weights=WEIGHTS,
            capacity=CAPACITY,
        )

        if result["feasible"]:
            feasible_count += 1

        if result["feasible"] and result["value"] == optimum_value:
            optimal_count += 1

    return {
        "feasible_probability": feasible_count / subset_count,
        "optimal_probability": optimal_count / subset_count,
        "subsets_enumerated": subset_count,
    }


def save_json(path, content):
    """Write JSON data using only JSON-compatible values."""
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(content, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def main():
    results_dir = ROOT / "results"
    tables_dir = results_dir / "tables"
    figures_dir = results_dir / "figures"
    data_dir = ROOT / "data" / "processed"

    for directory in (tables_dir, figures_dir, data_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Exact classical reference and random baseline
    # ---------------------------------------------------------
    (
        classical_optimum,
        qubo_ground_states,
        qubo_ground_energy,
    ) = classical_bruteforce()

    optimum_value = classical_optimum["value"]
    random_baseline = exact_random_baseline(optimum_value)

    print("Classical constrained optimum:", classical_optimum)
    print("Exact random baseline:", random_baseline)

    # ---------------------------------------------------------
    # 2. Optimize QAOA parameters using five seeded starts
    # ---------------------------------------------------------
    params = optimize_qaoa_grid(
        gamma_steps=25,
        beta_steps=25,
        num_starts=5,
        seed=0,
    )

    save_json(data_dir / "qaoa_optimization.json", params)

    print("\nSelected QAOA parameters:")
    print("  gamma:", params["gamma"])
    print("  beta:", params["beta"])
    print("  expected QUBO energy:", params["expected_qubo_energy"])
    print("  seeded starts:", len(params["starts"]))

    # ---------------------------------------------------------
    # 3. Build logical QAOA circuits
    # ---------------------------------------------------------
    logical = build_qaoa_circuit(
        params["gamma"],
        params["beta"],
    )

    logical_measured = build_qaoa_circuit(
        params["gamma"],
        params["beta"],
        measured=True,
    )

    # ---------------------------------------------------------
    # 4. Load processor configurations
    # ---------------------------------------------------------
    processor_configs = {
        "processor_B": load_processor("processor_B"),
        "processor_D": load_processor("processor_D"),
    }

    # Processor D coupling plot, when supported by the helper.
    processor_d = processor_configs["processor_D"]

    plot_coupling(
        processor_d,
        figures_dir / "processor_D_coupling.png",
    )

    metric_rows = []
    result_rows = []
    sampled_rows = []

    # ---------------------------------------------------------
    # 5. Transpile and simulate ideal/noisy Processor B and D
    # ---------------------------------------------------------
    for processor_name, config in processor_configs.items():
        transpiled = transpile_for_processor(logical_measured, config)

        metrics = circuit_metrics(
        logical_measured,
        transpiled,
        )

        metrics["processor"] = processor_name
        metric_rows.append(metrics)

        for condition in ("ideal", "noisy"):
            if condition == "ideal":
                simulator = AerSimulator()
            else:
                noise_model = build_noise_model(config)
                simulator = AerSimulator(noise_model=noise_model)

            # Keep runs reproducible.
            compiled = transpile_for_processor(logical_measured, config)

            job = simulator.run(
                compiled,
                shots=SHOTS,
                seed_simulator=SEED,
            )
            counts = job.result().get_counts()

            summary = summarize_counts(
            counts,
            optimum_value=optimum_value,
            )

            sampled_rows.append({
                "processor": processor_name,
                "condition": condition,
                "shots": SHOTS,
                **summary,
            })

            result_rows.append({
                "problem_id": "PS-O3",
                "processor": processor_name,
                "condition": condition,
                "executable": True,
                "logical_qubits": logical.num_qubits,
                "physical_qubits": config.get(
                    "num_qubits",
                    config.get("physical_qubits", logical.num_qubits),
                ),
                "logical_cx": metrics.get(
                    "logical_cx_equivalent",
                    metrics.get("logical_cx", ""),
                ),
                "cx": metrics.get("transpiled_cx_count", ""),
                "depth": metrics.get("transpiled_depth", ""),
                "two_q_depth": metrics.get("two_qubit_depth", ""),
                "swaps": metrics.get("estimated_routing_swaps", ""),
                "cx_overhead": metrics.get("cx_overhead", ""),
                "shots": SHOTS,
                "quality_metric": "feasible_shot_rate",
                "quality_value": summary.get("feasible_shot_rate", ""),
                "p_opt": summary.get("optimal_value_hit_rate", ""),
                "classical_optimum": optimum_value,
                "random_baseline": random_baseline["feasible_probability"],
            })

    # ---------------------------------------------------------
    # 6. Add Processor A non-executable row
    # ---------------------------------------------------------
    # Processor A has five qubits, while this problem requires nine.
    result_rows.append({
        "problem_id": "PS-O3",
        "processor": "Processor A",
        "condition": "not_applicable",
        "executable": False,
        "logical_qubits": logical.num_qubits,
        "physical_qubits": 5,
        "logical_cx": "",
        "cx": "",
        "depth": "",
        "two_q_depth": "",
        "swaps": "",
        "cx_overhead": "",
        "shots": 0,
        "quality_metric": "not_executable",
        "quality_value": "",
        "p_opt": "",
        "classical_optimum": optimum_value,
        "random_baseline": random_baseline["feasible_probability"],
    })

    # ---------------------------------------------------------
    # 7. Save tabular outputs
    # ---------------------------------------------------------
    metrics_df = pd.DataFrame(metric_rows)
    sampled_df = pd.DataFrame(sampled_rows)

    metrics_df.to_csv(
        tables_dir / "processor_metrics.csv",
        index=False,
    )

    sampled_df.to_csv(
        tables_dir / "sampled_results.csv",
        index=False,
    )

    with (tables_dir / "results.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=RESULT_COLUMNS,
        )
        writer.writeheader()
        writer.writerows(result_rows)

    # ---------------------------------------------------------
    # 8. Save circuit and processor comparison
    # ---------------------------------------------------------
    plot_comparison(
        metrics_df,
        figures_dir / "processor_comparison.png",
    )

    # ---------------------------------------------------------
    # 9. Processor D landscape
    # ---------------------------------------------------------
    # Required landscape range: gamma in [0, pi], beta in [0, pi].
    landscape = plot_o3_landscape(
        values=VALUES,
        weights=WEIGHTS,
        capacity=CAPACITY,
        output_path=figures_dir / "o3_solution_landscape.png",
        gamma_opt=params["gamma"],
        beta_opt=params["beta"],
        gamma_max=float(np.pi),
        gamma_steps=20,
        beta_steps=20,
        shots=1024,
        seed=SEED,
        processor_config=processor_d,
    )

    save_json(
        data_dir / "landscape_metadata.json",
        landscape,
    )

    # ---------------------------------------------------------
    # 10. Save experiment summary
    # ---------------------------------------------------------
    summary = {
        "problem_id": "PS-O3",
        "problem_statement": "Combinatorial 0-1 Knapsack Problem",
        "instance": {
            "values": VALUES,
            "weights": WEIGHTS,
            "capacity": CAPACITY,
        },
        "classical_constrained_optimum": classical_optimum,
        "qubo_ground_states": qubo_ground_states,
        "qubo_ground_energy": qubo_ground_energy,
        "qaoa_parameters": params,
        "random_baseline": random_baseline,
        "circuit_metrics": metric_rows,
        "ideal_and_noisy_sampled_results": sampled_rows,
        "landscape": landscape,
        "note": (
            "Results are from synthetic simulation, not real hardware. "
            "Processor A is not executable for this nine-qubit problem."
        ),
        "processor_A_status": (
            "Not executable for PS-O3: 9 logical qubits are required, "
            "but Processor A has only 5 physical qubits."
        ),
    }

    save_json(
        tables_dir / "benchmark_summary.json",
        summary,
    )

    save_json(
        tables_dir / "results_metadata.json",
        {
            "problem_id": "PS-O3",
            "classical_optimum": classical_optimum,
            "random_baseline": random_baseline,
            "result_columns": RESULT_COLUMNS,
        },
    )

    print("\nCircuit metrics:")
    print(metrics_df.to_string(index=False))

    print("\nIdeal/noisy sampled results:")
    print(sampled_df.to_string(index=False))

    print("\nOfficial CSV saved:", tables_dir / "results.csv")
    print("Landscape metadata saved:", data_dir / "landscape_metadata.json")


if __name__ == "__main__":
    main()
