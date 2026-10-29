
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
        config.get("coupling_map", []),
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
        f'{config["name"]} coupling graph ({num_qubits} qubits)'
    )
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_comparison(df, output_path):
    """Compare processor circuit resource metrics."""
    metrics = [
        "transpiled_depth",
        "transpiled_cx_count",
        "estimated_routing_swaps",
    ]

    fig, axes = plt.subplots(
        1,
        len(metrics),
        figsize=(12, 4),
    )

    for ax, metric in zip(axes, metrics):
        ax.bar(df["processor"], df[metric])
        ax.set_title(metric.replace("_", " ").title())
        ax.set_ylabel("Count / estimate")
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

    If processor_config is supplied, transpile to its coupling topology
    and simulate using its configured synthetic noise model.

    The gamma range automatically expands to include gamma_opt.
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
        raise ValueError(
            "The landscape requires at least a 20 x 20 grid."
        )

    if shots != 1024:
        raise ValueError(
            "The PS-O3 landscape requires 1024 shots per grid point."
        )

    if gamma_max <= 0:
        raise ValueError("gamma_max must be positive.")

    if gamma_opt is not None:
        if gamma_opt < 0:
            raise ValueError("gamma_opt must be non-negative.")

        # Ensure the selected gamma is included in the plot.
        gamma_max = max(float(gamma_max), float(gamma_opt))

    if beta_opt is not None and not 0 <= beta_opt <= np.pi:
        raise ValueError("beta_opt must be between 0 and pi.")

    gammas = np.linspace(
        0.0,
        float(gamma_max),
        gamma_steps,
    )
    betas = np.linspace(
        0.0,
        np.pi,
        beta_steps,
    )

    mean_energies = np.zeros(
        (beta_steps, gamma_steps),
        dtype=float,
    )

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
                circuit = transpile_for_processor(
                    circuit,
                    processor_config,
                )
            else:
                circuit = transpile(
                    circuit,
                    backend=simulator,
                )

            counts = (
                simulator.run(
                    circuit,
                    shots=shots,
                    seed_simulator=(
                        seed
                        + beta_index * gamma_steps
                        + gamma_index
                    ),
                )
                .result()
                .get_counts()
            )

            total_shots = sum(counts.values())

            if total_shots == 0:
                raise RuntimeError(
                    "No measurement counts returned for "
                    f"grid point ({gamma_index}, {beta_index})."
                )

            sampled_energy = 0.0

            for measured_bits, count in counts.items():
                # Qiskit count strings put classical bit 0 on the right.
                bits = [
                    int(bit)
                    for bit in measured_bits.replace(" ", "")[::-1]
                ]

                if len(bits) != N_QUBITS:
                    raise ValueError(
                        f"Expected {N_QUBITS} measured bits, "
                        f"received {len(bits)}."
                    )

                sampled_energy += (
                    float(qubo_energy(bits))
                    * count
                    / total_shots
                )

            mean_energies[beta_index, gamma_index] = (
                sampled_energy
            )

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
    )

    fig.colorbar(
        image,
        ax=ax,
        label="Sampled mean QUBO cost",
    )

    selected_point_inside_grid = False

    if gamma_opt is not None and beta_opt is not None:
        # Convert the NumPy comparison result to a native Python bool.
        selected_point_inside_grid = bool(
            gammas[0] <= gamma_opt <= gammas[-1]
            and betas[0] <= beta_opt <= betas[-1]
        )

        ax.scatter(
            [float(gamma_opt)],
            [float(beta_opt)],
            marker="*",
            s=200,
            edgecolors="black",
            label="Selected parameters",
            zorder=3,
        )
        ax.legend()

    ax.set_xlim(float(gammas[0]), float(gammas[-1]))
    ax.set_ylim(float(betas[0]), float(betas[-1]))
    ax.set_xlabel("Gamma")
    ax.set_ylabel("Beta")
    ax.set_title(
        "PS-O3 QAOA parameter landscape "
        f"({gamma_steps} x {beta_steps}, {shots} shots/point)"
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)

    # Explicitly convert values to native Python types for JSON serialization.
    return {
        "processor": (
            processor_config["name"]
            if processor_config is not None
            else "ideal"
        ),
        "noise_model": (
            "configured synthetic noise model"
            if processor_config is not None
            else "ideal simulator"
        ),
        "gamma_values": [float(value) for value in gammas],
        "beta_values": [float(value) for value in betas],
        "sampled_mean_qubo_cost": [
            [float(value) for value in row]
            for row in mean_energies
        ],
        "gamma_min": float(gammas[0]),
        "gamma_max": float(gammas[-1]),
        "beta_min": float(betas[0]),
        "beta_max": float(betas[-1]),
        "shots_per_point": int(shots),
        "grid_shape": [int(beta_steps), int(gamma_steps)],
        "selected_gamma": (
            float(gamma_opt)
            if gamma_opt is not None
            else None
        ),
        "selected_beta": (
            float(beta_opt)
            if beta_opt is not None
            else None
        ),
        "selected_point_inside_grid": bool(
            selected_point_inside_grid
        ),
        "seed": int(seed),
    }
