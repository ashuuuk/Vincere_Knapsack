"""Knapsack instance, quadratic penalty model, and classical verification."""
from itertools import product

VALUES = [10, 4, 7, 5, 8]
WEIGHTS = [5, 3, 4, 2, 6]
CAPACITY = 15
PENALTY = 1.0
LINEAR_WEIGHT_BIAS = 1.0


def evaluate_bits(bits, values=VALUES, weights=WEIGHTS, capacity=CAPACITY):
    """Evaluate a bit vector in item order x0..x(n-1)."""
    value = sum(v * int(x) for v, x in zip(values, bits))
    weight = sum(w * int(x) for w, x in zip(weights, bits))
    return {"bits": "".join(str(int(x)) for x in bits), "value": value,
            "weight": weight, "feasible": weight <= capacity}


def qubo_coefficients(values=VALUES, weights=WEIGHTS, capacity=CAPACITY,
                      penalty=PENALTY, linear_weight_bias=LINEAR_WEIGHT_BIAS):
    """Return E(x)=constant + sum(a[i]x[i]) + sum(b[i,j]x[i]x[j]).

    The objective is -value + penalty*(weight-capacity)^2
    + linear_weight_bias*(weight-capacity). The quadratic term discourages
    capacity deviation; the linear bias breaks the symmetry around capacity.
    Parameters are exposed so the penalty formulation can be justified/tuned.
    """
    n = len(values)
    linear = {}
    quadratic = {}
    constant = penalty * capacity**2 - linear_weight_bias * capacity
    for i, (v, w) in enumerate(zip(values, weights)):
        linear[i] = -v + penalty * w**2 - 2 * penalty * capacity * w + linear_weight_bias * w
        constant += 0.0
        for j in range(i + 1, n):
            quadratic[(i, j)] = 2 * penalty * weights[i] * weights[j]
    return constant, linear, quadratic


def qubo_energy(bits, values=VALUES, weights=WEIGHTS, capacity=CAPACITY,
                penalty=PENALTY, linear_weight_bias=LINEAR_WEIGHT_BIAS):
    value = sum(v * int(x) for v, x in zip(values, bits))
    weight = sum(w * int(x) for w, x in zip(weights, bits))
    return -value + penalty * (weight - capacity) ** 2 + linear_weight_bias * (weight - capacity)


def classical_bruteforce():
    """Return the exact constrained optimum and the QUBO ground state."""
    rows = [evaluate_bits(bits) for bits in product([0, 1], repeat=len(VALUES))]
    feasible = [r for r in rows if r["feasible"]]
    best_feasible = max(feasible, key=lambda r: (r["value"], -r["weight"]))
    qubo_rows = [(qubo_energy(bits), evaluate_bits(bits)) for bits in product([0, 1], repeat=len(VALUES))]
    best_qubo_energy = min(row[0] for row in qubo_rows)
    best_qubo = [row[1] for row in qubo_rows if abs(row[0] - best_qubo_energy) < 1e-9]
    return best_feasible, best_qubo, best_qubo_energy
