
"""Run reproducible PS-O3 QAOA experiments and save benchmark outputs."""

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from qff_phase2 import simulator as official_simulator, transpile_for
from src.problem import (
    VALUES,
    WEIGHTS,
    CAPACITY,
    N_ITEMS,
    N_QUBITS,
    classical_bruteforce,
    evaluate_bits,
)
from src.processors import load_processor, build_noise_model
from src.routing import build_qaoa_circuit, optimize_qaoa_grid
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
    "problem_id", "processor", "condition", "executable",
    "logical_qubits", "physical_qubits", "logical_cx", "cx",
    "depth", "two_q_depth", "swaps", "cx_overhead", "shots",
    "quality_metric", "quality_value", "p_opt", "classical_optimum",
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


def official_processor_config(config):
    """Normalize team processor data for the official QFF functions."""
    edges = config.get(
        "edges",
        config.get("coupling_map", config.get("coupling", [])),
    )
    num_qubits = config.get(
        "num_qubits",
        config.get("physical_qubits", N_QUBITS),
    )

    normalized = dict(config)
    normalized["name"] = config.get("name", "Unnamed processor")
    normalized["num_qubits"] = int(num_qubits)
    normalized["edges"] = [tuple(edge) for edge in edges]
    return normalized


def main():
    results_dir = ROOT / "results"
    tables_dir = results_dir / "tables"
    figures_dir = results_dir / "figures"
    data_dir = ROOT / "data" / "processed"

    for directory in (tables_dir, figures_dir, data_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # 1. Classical reference and random baseline.
    classical_optimum, qubo_ground_states, qubo_ground_energy = (
        classical_bruteforce()
    )
    optimum_value = classical_optimum["value"]
    random_baseline = exact_random_baseline(optimum_value)

    print("Classical constrained optimum:", classical_optimum)
    print("Exact random baseline:", random_baseline)

    # 2. Select parameters through the project's reproducible grid search.
    params = optimize_qaoa_grid(
        gamma_steps=25,
        beta_steps=25,
        num_starts=5,
        seed=0,
    )
    params["optimization_protocol"] = (
        "Five seeded local-grid searches plus a global grid search; "
        "selected parameters are used consistently for all outputs."
    )
    save_json(data_dir / "qaoa_optimization.json", params)

    print("\nSelected QAOA parameters:")
    print("  gamma:", params["gamma"])
    print("  beta:", params["beta"])
    print("  expected QUBO energy:", params["expected_qubo_energy"])

    # 3. Build logical circuits using the selected parameter pair.
    logical = build_qaoa_circuit(params["gamma"], params["beta"])
    logical_measured = build_qaoa_circuit(
        params["gamma"],
        params["beta"],
        measured=True,
    )

    # 4. Load processor configurations and normalize for official functions.
    processor_configs = {
        "processor_B": official_processor_config(load_processor("processor_B")),
        "processor_D": official_processor_config(load_processor("processor_D")),
    }
    processor_d = processor_configs["processor_D"]

    plot_coupling(processor_d, figures_dir / "processor_D_coupling.png")

    metric_rows = []
    result_rows = []
    sampled_rows = []

    # 5. Official metrics and ideal/noisy simulations.
    for _, config in processor_configs.items():
        processor_label = config["name"]
        metrics = circuit_metrics(logical, config)

        if not metrics.get("executable", False):
            raise RuntimeError(
                f"{processor_label} cannot execute the PS-O3 circuit: {metrics}"
            )

        metric_rows.append({**metrics, "processor": processor_label})

        # The official API requires a circuit already transpiled for the processor.
        compiled = transpile_for(logical_measured, config)

        conditions = {
            "ideal": official_simulator(
                noisy=False,
                processor=config,
            ),
            "noisy": official_simulator(
                noisy=True,
                processor=config,
                noise_model=build_noise_model(config),
            ),
        }

        for condition, simulator in conditions.items():
            counts = (
                simulator.run(
                    compiled,
                    shots=SHOTS,
                    seed_simulator=SEED,
                )
                .result()
                .get_counts()
            )

            sample_summary = summarize_counts(
                counts,
                optimum_value=optimum_value,
            )

            sampled_rows.append({
                "processor": processor_label,
                "condition": condition,
                "shots": SHOTS,
                **sample_summary,
            })

            result_rows.append({
                "problem_id": "PS-O3",
                "processor": processor_label,
                "condition": condition,
                "executable": True,
                "logical_qubits": metrics["logical_qubits"],
                "physical_qubits": metrics["physical_qubits"],
                "logical_cx": metrics["logical_cx"],
                "cx": metrics["cx"],
                "depth": metrics["depth"],
                "two_q_depth": metrics["two_q_depth"],
                "swaps": metrics["swaps"],
                "cx_overhead": metrics["cx_overhead"],
                "shots": SHOTS,
                "quality_metric": "feasible_shot_rate",
                "quality_value": sample_summary["feasible_shot_rate"],
                "p_opt": sample_summary["optimal_value_hit_rate"],
                "classical_optimum": optimum_value,
                "random_baseline": random_baseline["feasible_probability"],
            })

    # 6. Processor A has only five qubits and cannot execute this nine-qubit circuit.
    result_rows.append({
        "problem_id": "PS-O3",
        "processor": "Processor A",
        "condition": "not_applicable",
        "executable": False,
        "logical_qubits": N_QUBITS,
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

    # 7. Save the official result tables.
    metrics_df = pd.DataFrame(metric_rows)
    sampled_df = pd.DataFrame(sampled_rows)

    metrics_df.to_csv(tables_dir / "processor_metrics.csv", index=False)
    sampled_df.to_csv(tables_dir / "sampled_results.csv", index=False)

    with (tables_dir / "results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(result_rows)

    # 8. Compare actual official resource metrics.
    plot_comparison(
        metrics_df,
        figures_dir / "processor_comparison.png",
    )

    # 9. Landscape uses the SAME selected gamma and beta as the results.
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
    save_json(data_dir / "landscape_metadata.json", landscape)

    # 10. Save summary and matching parameter metadata.
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
            "Results use synthetic simulation, not real quantum hardware. "
            "Processor A cannot execute this nine-qubit problem."
        ),
        "processor_A_status": (
            "Not executable: PS-O3 requires nine logical qubits, "
            "but Processor A has five physical qubits."
        ),
    }
    save_json(tables_dir / "benchmark_summary.json", summary)

    save_json(
        tables_dir / "results_metadata.json",
        {
            "problem_id": "PS-O3",
            "classical_optimum": classical_optimum,
            "random_baseline": random_baseline,
            "result_columns": RESULT_COLUMNS,
            "qaoa_parameters": {
                "gamma": params["gamma"],
                "beta": params["beta"],
                "expected_qubo_energy": params["expected_qubo_energy"],
            },
            "shots_per_processor_condition": SHOTS,
            "seed": SEED,
        },
    )

    print("\nCircuit metrics:")
    print(metrics_df.to_string(index=False))
    print("\nIdeal/noisy sampled results:")
    print(
        sampled_df.drop(columns=["counts"], errors="ignore").to_string(
            index=False
        )
    )
    print("\nOfficial CSV saved:", tables_dir / "results.csv")
    print("Landscape metadata saved:", data_dir / "landscape_metadata.json")


if __name__ == "__main__":
    main()
