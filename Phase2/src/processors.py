
"""Processor topology and synthetic noise-model loaders."""

import json
from pathlib import Path

from qiskit.transpiler import CouplingMap
from qiskit_aer.noise import (
    NoiseModel,
    ReadoutError,
    depolarizing_error,
)

ROOT = Path(__file__).resolve().parents[1]


def load_processor(name):
    """Load a processor JSON and normalize its topology and noise fields."""

    path = ROOT / "processors" / f"{name}.json"

    with path.open(encoding="utf-8") as f:
        config = json.load(f)

    # Support both the original A/B format and the official D format.
    if "physical_qubits" in config:
        config["num_qubits"] = config["physical_qubits"]

    if "coupling_map" in config:
        edges = config["coupling_map"]
    elif "edges" in config:
        edges = config["edges"]
    else:
        raise ValueError(
            f"{name} must contain 'coupling_map' or 'edges'."
        )

    config["coupling_map"] = edges
    config["coupling"] = CouplingMap(
        [tuple(edge) for edge in edges]
    )

    # Normalize official D noise names to the existing A/B names.
    rates = config["noise"]

    if "single_qubit_depolarizing" not in rates:
        rates["single_qubit_depolarizing"] = rates["p1"]

    if "cx_depolarizing" not in rates:
        rates["cx_depolarizing"] = rates["p2"]

    if "readout_error" not in rates:
        rates["readout_error"] = rates["p_readout"]

    return config


def build_noise_model(config):
    """Build the synthetic depolarizing and readout noise model."""

    rates = config["noise"]

    noise = NoiseModel()

    one_qubit = depolarizing_error(
        rates["single_qubit_depolarizing"],
        1,
    )

    two_qubit = depolarizing_error(
        rates["cx_depolarizing"],
        2,
    )

    readout_p = rates["readout_error"]

    readout = ReadoutError(
        [
            [1 - readout_p, readout_p],
            [readout_p, 1 - readout_p],
        ]
    )

    noise.add_all_qubit_quantum_error(
        one_qubit,
        ["rz", "sx", "x"],
    )

    noise.add_all_qubit_quantum_error(
        two_qubit,
        ["cx"],
    )

    noise.add_all_qubit_readout_error(readout)

    return noise


def validate_processor_d(config, required_qubits):
    """Validate Processor D against the hackathon design rules."""

    errors = []

    # Rule 1: Qubit count
    num_qubits = config.get("num_qubits")

    if not isinstance(num_qubits, int) or not (
        required_qubits <= num_qubits <= 12
    ):
        errors.append(
            f"Qubit count must be between {required_qubits} and 12."
        )

    # Rule 2: Connectivity
    edges = config.get("edges", config.get("coupling_map", []))

    adjacency = {i: set() for i in range(num_qubits or 0)}

    for edge in edges:
        if len(edge) != 2:
            errors.append(f"Invalid edge: {edge}")
            continue

        a, b = edge

        if (
            not isinstance(a, int)
            or not isinstance(b, int)
            or a == b
            or a not in adjacency
            or b not in adjacency
        ):
            errors.append(f"Invalid edge: {edge}")
            continue

        adjacency[a].add(b)
        adjacency[b].add(a)

    if num_qubits and num_qubits > 0:
        visited = set()
        stack = [0]

        while stack:
            node = stack.pop()

            if node in visited:
                continue

            visited.add(node)
            stack.extend(adjacency[node] - visited)

        if len(visited) != num_qubits:
            errors.append("Coupling graph must be connected.")

    # Rule 3: Maximum degree
    for qubit, neighbors in adjacency.items():
        if len(neighbors) > 4:
            errors.append(
                f"Qubit {qubit} has degree {len(neighbors)}; maximum is 4."
            )

    # Rule 4: Exact gate set
    required_gates = {"rz", "sx", "x", "cx"}

    if set(config.get("basis_gates", [])) != required_gates:
        errors.append(
            "Basis gates must be exactly rz, sx, x, cx."
        )

    # Rule 5: Noise must not be better than official
    noise = config.get("noise", {})

    p1 = noise.get(
        "p1",
        noise.get("single_qubit_depolarizing", float("inf")),
    )

    p2 = noise.get(
        "p2",
        noise.get("cx_depolarizing", float("inf")),
    )

    p_readout = noise.get(
        "p_readout",
        noise.get("readout_error", float("inf")),
    )

    if p1 < 0.001:
        errors.append("Single-qubit noise cannot be below 0.001.")

    if p2 < 0.005:
        errors.append("CX noise cannot be below 0.005.")

    if p_readout < 0.01:
        errors.append("Readout noise cannot be below 0.01.")

    if errors:
        raise ValueError(
            "Processor D validation failed:\n- "
            + "\n- ".join(errors)
        )

    return True

