
"""PS-O3: Knapsack QUBO with 5 item bits and 4 slack bits."""

from itertools import product

VALUES = [10, 4, 7, 5, 8]
WEIGHTS = [5, 3, 4, 2, 6]
CAPACITY = 15
PENALTY = 5.0

N_ITEMS = len(VALUES)
SLACK_WEIGHTS = [1, 2, 4, 8]
N_SLACK = len(SLACK_WEIGHTS)
N_QUBITS = N_ITEMS + N_SLACK


def evaluate_bits(bits, values=VALUES, weights=WEIGHTS,
                  capacity=CAPACITY):
    """Evaluate item-selection bits only."""
    bits = [int(x) for x in bits]

    if len(bits) != len(values):
        raise ValueError("Expected one bit per item.")

    if any(x not in (0, 1) for x in bits):
        raise ValueError("Item bits must be binary.")

    value = sum(v * x for v, x in zip(values, bits))
    weight = sum(w * x for w, x in zip(weights, bits))

    return {
        "bits": "".join(map(str, bits)),
        "value": value,
        "weight": weight,
        "feasible": weight <= capacity,
    }


def split_bits(bits):
    """Split a 9-bit vector into item and slack bits."""
    bits = [int(x) for x in bits]

    if len(bits) != N_QUBITS:
        raise ValueError(f"Expected {N_QUBITS} bits.")

    if any(x not in (0, 1) for x in bits):
        raise ValueError("All bits must be binary.")

    return bits[:N_ITEMS], bits[N_ITEMS:]


def qubo_energy(bits, values=VALUES, weights=WEIGHTS,
                capacity=CAPACITY, penalty=PENALTY):
    """Energy = -value + P*(weight + slack - capacity)^2."""
    item_bits, slack_bits = split_bits(bits)

    value = sum(v * x for v, x in zip(values, item_bits))
    weight = sum(w * x for w, x in zip(weights, item_bits))
    slack = sum(w * x for w, x in zip(SLACK_WEIGHTS, slack_bits))

    return -value + penalty * (weight + slack - capacity) ** 2


def qubo_coefficients(values=VALUES, weights=WEIGHTS,
                      capacity=CAPACITY, penalty=PENALTY):
    """Return constant, linear and quadratic QUBO coefficients.

    E(z) = constant + sum(a[i]*z[i]) + sum(b[i,j]*z[i]*z[j])
    Variable order: item bits, then slack bits.
    """
    if len(values) != len(weights):
        raise ValueError("Values and weights must have equal lengths.")

    if len(values) != N_ITEMS:
        raise ValueError("Update the slack encoding for this item count.")

    coefficients = list(weights) + SLACK_WEIGHTS
    n = len(coefficients)

    linear = {}
    quadratic = {}
    constant = penalty * capacity**2

    for i, c_i in enumerate(coefficients):
        objective = -values[i] if i < len(values) else 0
        linear[i] = objective + penalty * (
            c_i**2 - 2 * capacity * c_i
        )

        for j in range(i + 1, n):
            quadratic[(i, j)] = (
                2 * penalty * c_i * coefficients[j]
            )

    return constant, linear, quadratic


def classical_bruteforce():
    """Find the exact constrained optimum and QUBO ground states."""
    item_rows = [
        evaluate_bits(bits)
        for bits in product((0, 1), repeat=N_ITEMS)
    ]

    feasible = [row for row in item_rows if row["feasible"]]
    best_feasible = max(
        feasible, key=lambda row: (row["value"], -row["weight"])
    )

    best_energy = float("inf")
    ground_states = []

    for bits in product((0, 1), repeat=N_QUBITS):
        energy = qubo_energy(bits)

        if energy < best_energy - 1e-9:
            best_energy = energy
            ground_states = [list(bits)]
        elif abs(energy - best_energy) < 1e-9:
            ground_states.append(list(bits))

    return best_feasible, ground_states, best_energy


if __name__ == "__main__":
    optimum, ground_states, energy = classical_bruteforce()
    print("Number of qubits:", N_QUBITS)
    print("Exact constrained optimum:", optimum)
    print("QUBO ground energy:", energy)
    print("QUBO ground states:", ground_states)
