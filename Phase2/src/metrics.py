"""Circuit metrics and sampled-result interpretation."""
from .problem import evaluate_bits


def circuit_metrics(logical_circuit, transpiled_circuit):
    logical_ops = logical_circuit.count_ops()
    physical_ops = transpiled_circuit.count_ops()
    logical_cx = int(logical_ops.get("cx", 0) + logical_ops.get("rzz", 0) * 2)
    physical_cx = int(physical_ops.get("cx", 0))
    # A routing-SWAP is commonly decomposed into ~3 CX gates; this is an
    # estimate, not a direct count of SWAP instructions after basis lowering.
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
    total = sum(counts.values())
    rows = []
    for measured_bits, count in counts.items():
        bits = [int(ch) for ch in measured_bits.replace(" ", "")][::-1]
        result = evaluate_bits(bits)
        rows.append({**result, "count": int(count), "probability": count / total})
    feasible_count = sum(r["count"] for r in rows if r["feasible"])
    best_feasible_value = max((r["value"] for r in rows if r["feasible"]), default=0)
    optimum_hits = sum(r["count"] for r in rows if r["feasible"] and r["value"] == 26 and r["weight"] == 14)
    most_common = max(rows, key=lambda r: r["count"])
    return {
        "shots": total,
        "feasible_shot_rate": feasible_count / total if total else 0.0,
        "best_feasible_value_sampled": best_feasible_value,
        "known_optimum_hit_rate": optimum_hits / total if total else 0.0,
        "most_common_bits": most_common["bits"],
        "most_common_value": most_common["value"],
        "most_common_weight": most_common["weight"],
        "counts": rows,
    }
