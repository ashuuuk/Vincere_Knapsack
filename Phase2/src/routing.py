
"""QAOA circuit construction and parameter optimization for PS-O3."""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

from src.problem import N_QUBITS, qubo_coefficients


def build_qaoa_circuit(gamma, beta, measured=False):
    """Build a p=1 QAOA circuit from the project's QUBO coefficients."""
    constant, linear, quadratic = qubo_coefficients()

    qc = QuantumCircuit(N_QUBITS)
    qc.h(range(N_QUBITS))

    # Convert x_i = (1 - Z_i) / 2 into Z and ZZ rotations.
    z_coefficients = np.zeros(N_QUBITS, dtype=float)
    zz_coefficients = {}

    for i, coefficient in linear.items():
        z_coefficients[i] -= float(coefficient) / 2.0

    for (i, j), coefficient in quadratic.items():
        coefficient = float(coefficient)
        z_coefficients[i] -= coefficient / 4.0
        z_coefficients[j] -= coefficient / 4.0
        zz_coefficients[(i, j)] = coefficient / 4.0

    for i, coefficient in enumerate(z_coefficients):
        if abs(coefficient) > 1e-12:
            qc.rz(2.0 * gamma * coefficient, i)

    for (i, j), coefficient in zz_coefficients.items():
        if abs(coefficient) > 1e-12:
            qc.rzz(2.0 * gamma * coefficient, i, j)

    # The QUBO constant only contributes a global phase, so it is omitted.
    for qubit in range(N_QUBITS):
        qc.rx(2.0 * beta, qubit)

    if measured:
        qc.measure_all()

    return qc


def expected_qubo_energy(gamma, beta):
    """Compute the exact ideal expected QUBO energy."""
    constant, linear, quadratic = qubo_coefficients()

    circuit = build_qaoa_circuit(gamma, beta)
    state = Statevector.from_instruction(circuit)
    probabilities = state.probabilities()

    expected_energy = 0.0

    for index, probability in enumerate(probabilities):
        # Qiskit statevector basis indices use little-endian qubit order.
        bits = [
            (index >> qubit) & 1
            for qubit in range(N_QUBITS)
        ]

        energy = float(constant)

        for i, coefficient in linear.items():
            energy += float(coefficient) * bits[i]

        for (i, j), coefficient in quadratic.items():
            energy += float(coefficient) * bits[i] * bits[j]

        expected_energy += float(probability) * energy

    return float(expected_energy)


def optimize_qaoa_grid(
    gamma_steps=25,
    beta_steps=25,
    num_starts=5,
    seed=0,
    local_radius=0.5,
):
    """
    Run five independent seeded local grid searches and a separate
    global grid search. Return the best result and every start's result.
    """
    if gamma_steps < 2 or beta_steps < 2:
        raise ValueError("Grid steps must be at least 2.")

    if num_starts < 1:
        raise ValueError("num_starts must be at least 1.")

    if local_radius <= 0:
        raise ValueError("local_radius must be positive.")

    def search(gamma_values, beta_values):
        best = None

        for gamma in gamma_values:
            for beta in beta_values:
                energy = expected_qubo_energy(
                    float(gamma),
                    float(beta),
                )

                candidate = {
                    "gamma": float(gamma),
                    "beta": float(beta),
                    "expected_qubo_energy": float(energy),
                }

                if (
                    best is None
                    or energy < best["expected_qubo_energy"]
                ):
                    best = candidate

        return best

    starts = []

    for start_index in range(num_starts):
        start_seed = int(seed + start_index)
        rng = np.random.default_rng(start_seed)

        initial_gamma, initial_beta = rng.uniform(
            0.0, np.pi, size=2
        )

        gamma_values = np.linspace(
            max(0.0, initial_gamma - local_radius),
            min(np.pi, initial_gamma + local_radius),
            gamma_steps,
        )

        beta_values = np.linspace(
            max(0.0, initial_beta - local_radius),
            min(np.pi, initial_beta + local_radius),
            beta_steps,
        )

        best = search(gamma_values, beta_values)

        starts.append({
            "start_index": start_index,
            "seed": start_seed,
            "initial_gamma": float(initial_gamma),
            "initial_beta": float(initial_beta),
            "best_gamma": best["gamma"],
            "best_beta": best["beta"],
            "best_expected_qubo_energy": (
                best["expected_qubo_energy"]
            ),
        })

    # A separate global grid provides a useful comparison against starts.
    global_best = search(
        np.linspace(0.0, np.pi, gamma_steps),
        np.linspace(0.0, np.pi, beta_steps),
    )

    candidates = [
        {
            "gamma": item["best_gamma"],
            "beta": item["best_beta"],
            "expected_qubo_energy": (
                item["best_expected_qubo_energy"]
            ),
        }
        for item in starts
    ]
    candidates.append(global_best)

    best_overall = min(
        candidates,
        key=lambda item: item["expected_qubo_energy"],
    )

    return {
        "gamma": best_overall["gamma"],
        "beta": best_overall["beta"],
        "expected_qubo_energy": (
            best_overall["expected_qubo_energy"]
        ),
        "seed": int(seed),
        "num_starts": int(num_starts),
        "gamma_steps": int(gamma_steps),
        "beta_steps": int(beta_steps),
        "method": (
            "independent seeded local grids plus a separate global grid"
        ),
        "starts": starts,
        "global_grid_best": global_best,
    }


def transpile_for_processor(circuit, config):
    """Transpile a circuit against a processor's gate and connectivity data."""
    if "basis_gates" not in config:
        raise KeyError("Missing basis_gates in processor configuration.")

    coupling = config.get("coupling", config.get("coupling_map"))

    if coupling is None:
        raise KeyError("Missing coupling or coupling_map.")

    return transpile(
        circuit,
        basis_gates=config["basis_gates"],
        coupling_map=coupling,
        optimization_level=int(config.get("optimization_level", 1)),
        seed_transpiler=int(config.get("seed_transpiler", 42)),
    )
