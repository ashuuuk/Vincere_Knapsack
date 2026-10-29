
"""Nine-qubit QAOA circuit construction and processor-aware transpilation."""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

from .problem import (
    N_QUBITS,
    qubo_coefficients,
    qubo_energy,
)


def build_qaoa_circuit(gamma, beta, measured=False):
    """Build a p=1 QAOA circuit for the complete nine-variable QUBO."""
    n = N_QUBITS
    _, linear, quadratic = qubo_coefficients()

    # Convert binary QUBO variables x=(I-Z)/2 into an Ising Hamiltonian.
    z_linear = {
        i: -linear[i] / 2.0
        for i in range(n)
    }
    zz = {
        ij: coeff / 4.0
        for ij, coeff in quadratic.items()
    }

    for (i, j), coeff in quadratic.items():
        z_linear[i] -= coeff / 4.0
        z_linear[j] -= coeff / 4.0

    qc = QuantumCircuit(n, n if measured else 0)

    # Initial equal superposition.
    qc.h(range(n))

    # Cost unitary.
    for i, coeff in z_linear.items():
        if abs(coeff) > 1e-12:
            qc.rz(2 * gamma * coeff, i)

    for (i, j), coeff in zz.items():
        if abs(coeff) > 1e-12:
            qc.rzz(2 * gamma * coeff, i, j)

    # Mixer unitary.
    for i in range(n):
        qc.rx(2 * beta, i)

    if measured:
        qc.measure(range(n), range(n))

    return qc


def optimize_qaoa_grid(gamma_steps=13, beta_steps=13):
    """Optimize p=1 parameters using an ideal statevector grid search."""
    best = None

    gammas = np.linspace(0.05, np.pi, gamma_steps)
    betas = np.linspace(0.05, np.pi / 2, beta_steps)

    for gamma in gammas:
        for beta in betas:
            circuit = build_qaoa_circuit(gamma, beta)
            state = Statevector.from_instruction(circuit)
            probabilities = state.probabilities()

            expected_energy = 0.0

            for index, probability in enumerate(probabilities):
                # Qiskit displays bitstrings with the highest-index bit first.
                bits = [
                    int(bit)
                    for bit in format(index, f"0{N_QUBITS}b")[::-1]
                ]
                expected_energy += (
                    float(probability) * qubo_energy(bits)
                )

            candidate = (
                expected_energy,
                float(gamma),
                float(beta),
            )

            if best is None or candidate[0] < best[0]:
                best = candidate

    return {
        "expected_qubo_energy": best[0],
        "gamma": best[1],
        "beta": best[2],
        "p": 1,
        "grid_gamma_steps": gamma_steps,
        "grid_beta_steps": beta_steps,
    }


def transpile_for_processor(circuit, config):
    """Transpile a circuit for the supplied processor configuration."""
    return transpile(
        circuit,
        basis_gates=config["basis_gates"],
        coupling_map=config["coupling"],
        optimization_level=config["optimization_level"],
        seed_transpiler=config["seed_transpiler"],
    )
