
"""Plots for processor topology, comparisons, and the PS-O3 QAOA landscape."""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def plot_coupling(config, output_path):
    """Plot a processor's physical coupling graph."""
    graph = nx.Graph()

    num_qubits = config.get(
        "num_qubits",
        config.get("physical_qubits"),
    )
    edges = config.get(
        "edges",
        config.get("coupling_map", config.get("coupling", [])),
    )

    if num_qubits is None:
        raise ValueError("Processor configuration must specify qubit count.")

    graph.add_nodes_from(range(int(num_qubits)))
    graph.add_edges_from([tuple(edge) for edge in edges])

    pos = nx.spring_layout(graph, seed=42)

    fig, ax = plt.subplots(figsize=(6, 4))
    nx.draw_networkx(
        graph,
        pos=pos,
        ax=ax,
        with_labels=True,
        node_size=700,
        font_size=10,
    )

    ax.set_title(
        f'{config.get("name", "Processor")} coupling graph ({num_qubits} qubits)'
    )
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_comparison(df, output_path):
    """Compare processor circuit resource metrics using official values."""
    metrics = [
        ("depth", "Transpiled circuit depth"),
        ("cx", "Physical CX count"),
        ("swaps", "Actual routing SWAP count"),
    ]

    fig, axes = plt.subplots(1, len(metrics), figsize=(12, 4))

    for ax, (metric, title) in zip(axes, metrics):
        if metric not in df.columns:
            raise ValueError(
                f"Missing required metric column '{metric}'. "
                f"Available columns: {list(df.columns)}"
            )

        ax.bar(df["processor"], df[metric])
        ax.set_title(title)
        ax.set_ylabel("Count")
        ax.tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_o3_landscape(
    values,
    weights,
    capacity,
    output_path,
    gamma_opt=None,
    beta_opt=None,
    gamma_max=0.1,
    gamma_steps=20,
    beta_steps=20,
    shots=1024,
    seed=42,
    processor_config=None,
):
    """
    Plot sampled mean QUBO cost across a gamma/beta parameter grid.

    The landscape uses at least a 20 x 20 grid and 1024 shots per point.
    If a processor configuration is provided, its topology and noise model
    are used for the landscape simulation.
    """
    from qiskit import transpile
    from qiskit_aer import AerSimulator

    from .processors import build_noise_model
    from .problem import N_QUBITS, qubo_energy
    from .routing import (
        build_qaoa_circuit,
        transpile_for_processor,
    )

    if gamma_steps < 20 or beta_steps < 20:
        raise ValueError("The landscape requires at least a 20 x 20 grid.")

    if shots != 1024:
        raise ValueError("The PS-O3 landscape requires 1024 shots per grid point.")

    if gamma_max <= 0:
        raise ValueError("gamma_max must be positive.")

    if gamma_opt is not None:
        if gamma_opt < 0:
            raise ValueError("gamma_opt must be non-negative.")
        gamma_max = max(float(gamma_max), float(gamma_opt))

    if beta_opt is not None and not 0 <= beta_opt <= np.pi:
        raise ValueError("beta_opt must be between 0 and pi.")

    gammas = np.linspace(0.0, float(gamma_max), gamma_steps)
    betas = np.linspace(0.0, np.pi, beta_steps)

    mean_energies = np.zeros((beta_steps, gamma_steps), dtype=float)

    noise_model = (
        build_noise_model(processor_config)
        if processor_config is not None
        else None
    )
    simulator = AerSimulator(noise_model=noise_model)

    for beta_index, beta in enumerate(betas):
        for gamma_index, gamma in enumerate(gammas):
            circuit = build_qaoa_circuit(
                float(gamma),
                float(beta),
                measured=True,
            )

            if processor_config is not None:
                circuit = transpile_for_processor(circuit, processor_config)
            else:
                circuit = transpile(
                    circuit,
                    backend=simulator,
                    seed_transpiler=42,
                    optimization_level=1,
                )

            counts = (
                simulator.run(
                    circuit,
                    shots=shots,
                    seed_simulator=seed + beta_index * gamma_steps + gamma_index,
                )
                .result()
                .get_counts()
            )

            total_shots = sum(counts.values())
            if total_shots == 0:
                raise RuntimeError(
                    f"No counts returned for grid point "
                    f"({gamma_index}, {beta_index})."
                )

            sampled_energy = 0.0

            for measured_bits, count in counts.items():
                bits = [
                    int(bit)
                    for bit in measured_bits.replace(" ", "")[::-1]
                ]

                if len(bits) != N_QUBITS:
                    raise ValueError(
                        f"Expected {N_QUBITS} measured bits, received {len(bits)}."
                    )

                sampled_energy += (
                    float(qubo_energy(bits)) * count / total_shots
                )

            mean_energies[beta_index, gamma_index] = sampled_energy

    fig, ax = plt.subplots(figsize=(9, 6))

    image = ax.imshow(
        mean_energies,
        origin="lower",
        aspect="auto",
        extent=[
            float(gammas[0]),
            float(gammas[-1]),
            float(betas[0]),
            float(betas[-1]),
        ],
        cmap="viridis",
    )

    fig.colorbar(image, ax=ax, label="Mean QUBO energy")
    ax.set_xlabel("Gamma")
    ax.set_ylabel("Beta")
    ax.set_title("PS-O3 QAOA solution landscape")

    if gamma_opt is not None and beta_opt is not None:
        ax.scatter(
            [gamma_opt],
            [beta_opt],
            color="red",
            marker="x",
            s=100,
            label="Selected parameters",
        )
        ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)

    metadata = {
        "gamma_min": float(gammas[0]),
        "gamma_max": float(gammas[-1]),
        "beta_min": float(betas[0]),
        "beta_max": float(betas[-1]),
        "gamma_steps": int(gamma_steps),
        "beta_steps": int(beta_steps),
        "shots_per_point": int(shots),
        "seed": int(seed),
        "selected_gamma": (
            float(gamma_opt) if gamma_opt is not None else None
        ),
        "selected_beta": (
            float(beta_opt) if beta_opt is not None else None
        ),
        "processor": (
            processor_config.get("name")
            if processor_config is not None
            else "ideal",
        ),
    }

    return metadata
