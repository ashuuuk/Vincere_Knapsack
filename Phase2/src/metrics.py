
"""Circuit metrics and nine-bit knapsack result interpretation."""

from .problem import (
    N_ITEMS,
    N_QUBITS,
    VALUES,
    WEIGHTS,
    CAPACITY,
    evaluate_bits,
)


def circuit_metrics(logical_circuit, processor):
    """Use the official QFF Phase 2 circuit metric definitions."""
    from qff_phase2 import circuit_metrics as official_circuit_metrics

    official_processor = dict(processor)
    official_processor["num_qubits"] = int(
        processor["num_qubits"]
        if "num_qubits" in processor
        else processor["physical_qubits"]
    )
    official_processor["edges"] = [
        tuple(edge)
        for edge in processor.get(
            "edges",
            processor.get("coupling_map", processor.get("coupling", [])),
        )
    ]

    return official_circuit_metrics(logical_circuit, official_processor)


def summarize_counts(counts, optimum_value):
    """Summarize measured solutions against the classical optimum."""
    total = sum(counts.values())
    if total == 0:
        raise ValueError("No measurement counts were provided.")

    rows = []

    for measured_bits, count in counts.items():
        bits = [
            int(ch)
            for ch in measured_bits.replace(" ", "")[::-1]
        ]

        if len(bits) != N_QUBITS:
            raise ValueError(
                f"Expected {N_QUBITS} measured bits, got {len(bits)}."
            )

        item_bits = bits[:N_ITEMS]
        slack_bits = bits[N_ITEMS:]

        result = evaluate_bits(
            item_bits,
            values=VALUES,
            weights=WEIGHTS,
            capacity=CAPACITY,
        )

        slack_value = sum(
            bit * (2 ** i) for i, bit in enumerate(slack_bits)
        )

        rows.append({
            **result,
            "slack_bits": "".join(map(str, slack_bits)),
            "slack_value": slack_value,
            "count": int(count),
            "probability": count / total,
        })

    feasible_count = sum(
        row["count"] for row in rows if row["feasible"]
    )

    best_feasible_value = max(
        (row["value"] for row in rows if row["feasible"]),
        default=0,
    )

    optimum_hits = sum(
        row["count"]
        for row in rows
        if row["feasible"] and row["value"] == optimum_value
    )

    most_common = max(rows, key=lambda row: row["count"])

    return {
        "shots": total,
        "feasible_shot_rate": feasible_count / total,
        "best_feasible_value_sampled": best_feasible_value,
        "optimal_value_hit_rate": optimum_hits / total,
        "most_common_bits": most_common["bits"],
        "most_common_value": most_common["value"],
        "most_common_weight": most_common["weight"],
        "counts": rows,
    }
