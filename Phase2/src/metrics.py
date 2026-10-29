
"""Circuit metrics and nine-bit knapsack result interpretation."""

from .problem import (
    N_ITEMS,
    N_QUBITS,
    VALUES,
    WEIGHTS,
    CAPACITY,
    evaluate_bits,
)


def circuit_metrics(logical_circuit, transpiled_circuit):
    logical_ops = logical_circuit.count_ops()
    physical_ops = transpiled_circuit.count_ops()

    logical_cx = int(
        logical_ops.get("cx", 0) + logical_ops.get("rzz", 0) * 2
    )
    physical_cx = int(physical_ops.get("cx", 0))

    swap_estimate = max(0.0, (physical_cx - logical_cx) / 3.0)

    return {
        "logical_depth": int(logical_circuit.depth()),
        "transpiled_depth": int(transpiled_circuit.depth()),
        "logical_cx_equivalent": logical_cx,
        "transpiled_cx_count": physical_cx,
        "estimated_routing_swaps": round(swap_estimate, 2),
        "transpiled_operation_count": int(sum(physical_ops.values())),
    }


def summarize_counts(counts):
    """Evaluate feasibility using item bits only; retain slack bits."""
    total = sum(counts.values())
    if total == 0:
        raise ValueError("No measurement counts were provided.")

    rows = []

    for measured_bits, count in counts.items():
        # Qiskit count strings place classical bit 0 at the right.
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

    optimum_value = max(
        row["value"] for row in rows if row["feasible"]
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
