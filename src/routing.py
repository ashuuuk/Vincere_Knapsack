"""QAOA circuit construction and processor-aware transpilation."""
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from .problem import qubo_coefficients


def build_qaoa_circuit(gamma, beta, measured=False):
    n = 5
    _, linear, quadratic = qubo_coefficients()
    # Convert x_i=(I-Z_i)/2 into Ising coefficients. Global identity terms
    # affect only global phase and can be omitted from the circuit.
    z_linear = {i: -linear[i] / 2 for i in range(n)}
    zz = {ij: coeff / 4 for ij, coeff in quadratic.items()}
    for (i, j), coeff in quadratic.items():
        z_linear[i] -= coeff / 4
        z_linear[j] -= coeff / 4

    qc = QuantumCircuit(n, n if measured else 0)
    qc.h(range(n))
    for i, coeff in z_linear.items():
        qc.rz(2 * gamma * coeff, i)
    for (i, j), coeff in zz.items():
        qc.rzz(2 * gamma * coeff, i, j)
    for i in range(n):
        qc.rx(2 * beta, i)
    if measured:
        qc.measure(range(n), range(n))
    return qc


def optimize_qaoa_grid(gamma_steps=13, beta_steps=13):
    """Small deterministic p=1 grid search on the ideal statevector."""
    from .problem import qubo_energy
    best = None
    gammas = np.linspace(0.05, np.pi, gamma_steps)
    betas = np.linspace(0.05, np.pi / 2, beta_steps)
    for gamma in gammas:
        for beta in betas:
            state = Statevector.from_instruction(build_qaoa_circuit(gamma, beta))
            probs = state.probabilities()
            expected = 0.0
            for index, prob in enumerate(probs):
                bits = format(index, "05b")[::-1]
                expected += float(prob) * qubo_energy([int(b) for b in bits])
            if best is None or expected < best[0]:
                best = (expected, float(gamma), float(beta))
    return {"expected_qubo_energy": best[0], "gamma": best[1], "beta": best[2]}


def transpile_for_processor(circuit, config):
    return transpile(
        circuit,
        basis_gates=config["basis_gates"],
        coupling_map=config["coupling"],
        optimization_level=config["optimization_level"],
        seed_transpiler=config["seed_transpiler"],
    )
