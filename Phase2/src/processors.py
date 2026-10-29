
"""Processor configuration loading, validation, and Aer noise models."""

import json
from pathlib import Path

import networkx as nx
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError


def load_processor(path):
    """Load official or legacy processor configuration."""
    path = Path(path)

    if not path.is_file():
        candidates = [
            Path("processors") / f"{path.name}.json",
            Path("processors") / path.name,
        ]
        for candidate in candidates:
            if candidate.is_file():
                path = candidate
                break

    if not path.is_file():
        raise FileNotFoundError(
            f"Processor configuration not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    # Normalize processor topology fields for the rest of the project.
    config["physical_qubits"] = config.get(
        "num_qubits", config.get("physical_qubits")
    )
    config["coupling_map"] = config.get(
        "edges", config.get("coupling_map", config.get("coupling", []))
    )

    # Different modules in this project use different topology key names.
    config["coupling"] = config["coupling_map"]

    raw_noise = config.get("noise", {})
    config["noise"] = {
        "single_qubit_depolarizing": raw_noise.get(
            "p1", raw_noise.get("single_qubit_depolarizing", 0.001)
        ),
        "cx_depolarizing": raw_noise.get(
            "p2", raw_noise.get("cx_depolarizing", 0.005)
        ),
        "readout_error": raw_noise.get(
            "p_readout", raw_noise.get("readout_error", 0.01)
        ),
    }

    config.setdefault("optimization_level", 1)
    config.setdefault("seed_transpiler", 42)
    config.setdefault("shots", 4096)

    return config


def validate_processor_d(config, required_qubits=9):
    """Validate Processor D against Phase 2 requirements."""
    n = config.get("physical_qubits", config.get("num_qubits"))
    edges = config.get("coupling_map", config.get("edges", []))

    if n is None or int(n) != required_qubits:
        raise ValueError(
            f"Processor D must have exactly {required_qubits} qubits."
        )

    graph = nx.Graph()
    graph.add_nodes_from(range(int(n)))
    graph.add_edges_from(tuple(edge) for edge in edges)

    if not nx.is_connected(graph):
        raise ValueError(
            "Processor D coupling graph must be connected."
        )

    if max(dict(graph.degree()).values(), default=0) > 4:
        raise ValueError(
            "Processor D maximum degree must be at most 4."
        )

    if config.get("basis_gates") != ["rz", "sx", "x", "cx"]:
        raise ValueError(
            'basis_gates must be exactly ["rz", "sx", "x", "cx"].'
        )

    noise = config.get("noise", {})
    p1 = noise.get("p1", noise.get("single_qubit_depolarizing", 0))
    p2 = noise.get("p2", noise.get("cx_depolarizing", 0))
    readout = noise.get(
        "p_readout", noise.get("readout_error", 0)
    )

    if p1 < 0.001 or p2 < 0.005 or readout < 0.01:
        raise ValueError(
            "Processor D noise is below the required minimum."
        )

    return True


def build_noise_model(config):
    """Build an Aer noise model from normalized processor settings."""
    noise = config["noise"]

    p1 = noise["single_qubit_depolarizing"]
    p2 = noise["cx_depolarizing"]
    readout = noise["readout_error"]

    model = NoiseModel()

    if p1 > 0:
        model.add_all_qubit_quantum_error(
            depolarizing_error(p1, 1), ["sx", "x"]
        )

    if p2 > 0:
        model.add_all_qubit_quantum_error(
            depolarizing_error(p2, 2), ["cx"]
        )

    if readout > 0:
        model.add_all_qubit_readout_error(
            ReadoutError([
                [1 - readout, readout],
                [readout, 1 - readout],
            ])
        )

    return model

