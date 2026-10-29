"""Generate the official PS-O3 processor comparison CSV."""

import csv
import json
from pathlib import Path

from qff_phase2 import simulator as official_simulator, transpile_for

from src.problem import (
    VALUES,
    WEIGHTS,
    CAPACITY,
    N_ITEMS,
    classical_bruteforce,
    evaluate_bits,
)
from src.processors import load_processor, build_noise_model
from src.routing import build_qaoa_circuit, optimize_qaoa_grid
from src.metrics import circuit_metrics, summarize_counts

ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "results" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

SHOTS = 4096
SEED = 42

COLUMNS = [
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
    """Enumerate all 32 item subsets with equal probability."""
    feasible = 0
    optimal = 0

    for mask in range(1 << N_ITEMS):
        bits = [(mask >> i) & 1 for i in range(N_ITEMS)]
        result = evaluate_bits(
            bits,
            values=VALUES,
            weights=WEIGHTS,
            capacity=CAPACITY,
        )

        if result["feasible"]:
            feasible += 1

        if result["feasible"] and result["value"] == optimum_value:
            optimal += 1

    return feasible / (1 << N_ITEMS), optimal / (1 << N_ITEMS)


def main():
    classical_optimum, _, _ = classical_bruteforce()
    optimum_value = classical_optimum["value"]
    random_feasible, random_optimal = exact_random_baseline(optimum_value)

    params = optimize_qaoa_grid()
    logical = build_qaoa_circuit(params["gamma"], params["beta"])
    measured = build_qaoa_circuit(
        params["gamma"], params["beta"], measured=True
    )

    rows = []

    # Processor A cannot execute a nine-qubit PS-O3 circuit.
    rows.append({
        "problem_id": "PS-O3",
        "processor": "Processor A",
        "condition": "not_applicable",
        "executable": False,
        "logical_qubits": 9,
        "physical_qubits": 5,
        "logical_cx": "",
        "cx": "",
        "depth": "",
        "two_q_depth": "",
        "swaps": "",
        "cx_overhead": "",
        "shots": 0,
        "quality_metric": "feasible_shot_rate",
        "quality_value": "",
        "p_opt": "",
        "classical_optimum": optimum_value,
        "random_baseline": random_feasible,
    })

    for processor_name in ("processor_B", "processor_D"):
        config = load_processor(processor_name)
        official_config = {
            "name": config["name"],
            "num_qubits": config["physical_qubits"],
            "edges": [tuple(edge) for edge in config["coupling_map"]],
        }
        compiled = transpile_for(measured, official_config)
        metrics = circuit_metrics(logical, official_config)

        conditions = {
            "ideal": official_simulator(noisy=False, processor=official_config),
            "noisy": official_simulator(
                noisy=True,
                processor=official_config,
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

            summary = summarize_counts(counts, optimum_value)

            # Keep ideal/noisy sample counts for reproducibility.
            count_file = TABLES / (
                f"{processor_name}_{condition}_counts.csv"
            )
            import pandas as pd
            pd.DataFrame(summary["counts"]).to_csv(count_file, index=False)

            logical_cx = metrics["logical_cx"]
            physical_cx = metrics["cx"]

            rows.append({
                "problem_id": "PS-O3",
                "processor": config["name"],
                "condition": condition,
                "executable": True,
                "logical_qubits": metrics["logical_qubits"],
                "physical_qubits": metrics["physical_qubits"],
                "logical_cx": logical_cx,
                "cx": physical_cx,
                "depth": metrics["depth"],
                "two_q_depth": metrics["two_q_depth"],
                "swaps": metrics["swaps"],
                "cx_overhead": metrics["cx_overhead"],
                "shots": summary["shots"],
                "quality_metric": "feasible_shot_rate",
                "quality_value": summary["feasible_shot_rate"],
                "p_opt": summary["optimal_value_hit_rate"],
                "classical_optimum": optimum_value,
                "random_baseline": random_feasible,
            })

    output = TABLES / "results.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "problem_id": "PS-O3",
        "classical_optimum": classical_optimum,
        "random_baseline_feasible_probability": random_feasible,
        "random_baseline_optimal_probability": random_optimal,
        "random_baseline_method": (
            "Exact enumeration of all 32 equally likely item subsets"
        ),
        "qaoa_parameters": params,
        "shots_per_processor_condition": SHOTS,
        "seed": SEED,
        "limitations": [
            "Simulated results, not real hardware measurements.",
            "Random baseline is the probability of a uniformly random "
            "item subset being feasible.",
        ],
    }

    (TABLES / "results_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"Saved: {output}")
    print(f"Exact random feasible baseline: {random_feasible:.6f}")
    print(f"Exact random optimal baseline: {random_optimal:.6f}")
    print("\nGenerated results:")
    for row in rows:
        print(
            row["processor"],
            row["condition"],
            "executable =", row["executable"],
            "feasible rate =", row["quality_value"],
            "P_opt =", row["p_opt"],
        )


if __name__ == "__main__":
    main()
