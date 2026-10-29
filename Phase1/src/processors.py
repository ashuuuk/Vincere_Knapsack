"""Processor topology and synthetic noise-model loaders."""
import json
from pathlib import Path
from qiskit.transpiler import CouplingMap
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

ROOT = Path(__file__).resolve().parents[1]


def load_processor(name):
    path = ROOT / "processors" / f"{name}.json"
    with path.open(encoding="utf-8") as f:
        config = json.load(f)
    config["coupling"] = CouplingMap(
    [tuple(e) for e in config["coupling_map"]]
)
    return config


def build_noise_model(config):
    rates = config["noise"]
    noise = NoiseModel()
    one_qubit = depolarizing_error(rates["single_qubit_depolarizing"], 1)
    two_qubit = depolarizing_error(rates["cx_depolarizing"], 2)
    readout_p = rates["readout_error"]
    readout = ReadoutError([[1 - readout_p, readout_p], [readout_p, 1 - readout_p]])
    noise.add_all_qubit_quantum_error(one_qubit, ["rz", "sx", "x"])
    noise.add_all_qubit_quantum_error(two_qubit, ["cx"])
    noise.add_all_qubit_readout_error(readout)
    return noise
