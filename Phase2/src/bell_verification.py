
"""
Bell-state verification for Vincere_Knapsack.

Runs Bell verification on Processor D:
- Adjacent pair: (0, 1), distance 1
- Farthest pair: (0, 6), distance 3
- Ideal and configured synthetic-noise simulations
- XX, YY, ZZ measurement bases
"""

import csv
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from processors import load_processor, build_noise_model


SHOTS = 4096
BASES = ["XX", "YY", "ZZ"]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "results" / "tables"
OUTPUT_FILE = OUTPUT_DIR / "bell.csv"

PROCESSOR_NAME = "processor_D"

PAIRS = [
    {"name": "adjacent", "qubits": (0, 1), "distance": 1},
    {"name": "farthest", "qubits": (0, 6), "distance": 3},
]


def create_bell_circuit(basis: str) -> QuantumCircuit:
    """Create a two-qubit Bell circuit for a requested measurement basis."""

    qc = QuantumCircuit(2, 2)

    qc.h(0)
    qc.cx(0, 1)

    if basis == "XX":
        qc.h(0)
        qc.h(1)

    elif basis == "YY":
        qc.sdg(0)
        qc.sdg(1)
        qc.h(0)
        qc.h(1)

    elif basis == "ZZ":
        pass

    else:
        raise ValueError("Invalid basis. Choose XX, YY or ZZ.")

    qc.measure([0, 1], [0, 1])

    return qc


def calculate_correlation(counts: dict) -> float:
    """Calculate parity correlation from two-bit measurement counts."""

    total_shots = sum(counts.values())
    correlation = 0.0

    for bitstring, count in counts.items():
        bitstring = bitstring.replace(" ", "")

        if bitstring[0] == bitstring[1]:
            correlation += count
        else:
            correlation -= count

    return correlation / total_shots


def calculate_standard_error(correlation: float, shots: int) -> float:
    return np.sqrt(max(0.0, 1.0 - correlation**2) / shots)


def calculate_fidelity(xx: float, yy: float, zz: float) -> float:
    return (1.0 + xx - yy + zz) / 4.0


def calculate_fidelity_se(
    xx_se: float,
    yy_se: float,
    zz_se: float,
) -> float:
    return np.sqrt(xx_se**2 + yy_se**2 + zz_se**2) / 4.0


def run_one_pair(processor, pair, noisy: bool):
    """Run XX, YY and ZZ for one selected physical pair."""

    physical_pair = pair["qubits"]

    simulator = (
        AerSimulator(noise_model=build_noise_model(processor))
        if noisy
        else AerSimulator()
    )

    results = {}
    cx_count = None

    for basis in BASES:
        logical_circuit = create_bell_circuit(basis)

        # Map the two logical qubits onto the selected physical pair.
        initial_layout = list(physical_pair)

        transpiled_circuit = transpile(
            logical_circuit,
            basis_gates=processor["basis_gates"],
            coupling_map=processor["coupling"],
            initial_layout=initial_layout,
            optimization_level=1,
            seed_transpiler=42,
        )

        if cx_count is None:
            cx_count = transpiled_circuit.count_ops().get("cx", 0)

        counts = simulator.run(
            transpiled_circuit,
            shots=SHOTS,
        ).result().get_counts()

        correlation = calculate_correlation(counts)
        standard_error = calculate_standard_error(
            correlation,
            SHOTS,
        )

        results[basis] = {
            "correlation": correlation,
            "standard_error": standard_error,
            "counts": counts,
        }

    xx = results["XX"]["correlation"]
    yy = results["YY"]["correlation"]
    zz = results["ZZ"]["correlation"]

    xx_se = results["XX"]["standard_error"]
    yy_se = results["YY"]["standard_error"]
    zz_se = results["ZZ"]["standard_error"]

    fidelity = calculate_fidelity(xx, yy, zz)
    fidelity_se = calculate_fidelity_se(xx_se, yy_se, zz_se)

    return {
        "results": results,
        "fidelity": fidelity,
        "fidelity_se": fidelity_se,
        "cx_count": cx_count,
    }


def save_results(rows):
    """Save one row per pair, noise setting and measurement basis."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "pair_name",
        "physical_qubits",
        "distance",
        "transpiled_cx_count",
        "basis",
        "correlation",
        "standard_error",
        "shots",
        "fidelity",
        "fidelity_se",
        "processor",
        "noise",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults saved to: {OUTPUT_FILE}")


def run_bell_verification():
    processor = load_processor(PROCESSOR_NAME)

    all_rows = []

    print("\nProcessor D Bell-State Verification")
    print("=" * 60)

    for pair in PAIRS:
        for noisy in [False, True]:
            label = "noisy" if noisy else "ideal"

            outcome = run_one_pair(processor, pair, noisy)

            print(
                f"\nPair {pair['qubits']} | "
                f"distance={pair['distance']} | {label}"
            )

            for basis in BASES:
                result = outcome["results"][basis]

                print(
                    f"{basis}: "
                    f"{result['correlation']:.4f} "
                    f"+/- {result['standard_error']:.4f}"
                )

                all_rows.append({
                    "pair_name": pair["name"],
                    "physical_qubits": str(pair["qubits"]),
                    "distance": pair["distance"],
                    "transpiled_cx_count": outcome["cx_count"],
                    "basis": basis,
                    "correlation": result["correlation"],
                    "standard_error": result["standard_error"],
                    "shots": SHOTS,
                    "fidelity": outcome["fidelity"],
                    "fidelity_se": outcome["fidelity_se"],
                    "processor": PROCESSOR_NAME,
                    "noise": label,
                })

            print(
                f"Bell Fidelity: {outcome['fidelity']:.4f} "
                f"+/- {outcome['fidelity_se']:.4f}"
            )

    save_results(all_rows)

    return all_rows


if __name__ == "__main__":
    run_bell_verification()
