"""Plots for processor topology and benchmark comparisons."""
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx


def plot_coupling(config, output_path):
    graph = nx.Graph()
    graph.add_nodes_from(range(config["physical_qubits"]))
    graph.add_edges_from([tuple(e) for e in config["coupling_map"]])
    pos = nx.spring_layout(graph, seed=42)
    plt.figure(figsize=(6, 4))
    nx.draw_networkx(graph, pos=pos, with_labels=True, node_size=700, font_size=10)
    plt.title(f'{config["name"]} coupling graph ({config["physical_qubits"]} qubits)')
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_comparison(df, output_path):
    metrics = ["transpiled_depth", "transpiled_cx_count", "estimated_routing_swaps"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(12, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(df["processor"], df[metric])
        ax.set_title(metric.replace("_", " ").title())
        ax.set_ylabel("Count / estimate")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)

def plot_o3_landscape(values, weights, capacity, output_path):
    """Plot all 32 item subsets by weight and value, highlighting feasible solutions."""
    import itertools

    points = []
    for bits in itertools.product([0, 1], repeat=len(values)):
        weight = sum(b * w for b, w in zip(bits, weights))
        value = sum(b * v for b, v in zip(bits, values))
        points.append((weight, value, weight <= capacity))

    plt.figure(figsize=(8, 5))
    for feasible, label in [(True, "Feasible"), (False, "Infeasible")]:
        subset = [p for p in points if p[2] == feasible]
        plt.scatter(
            [p[0] for p in subset],
            [p[1] for p in subset],
            label=label,
            alpha=0.75,
        )

    plt.axvline(capacity, linestyle="--", label=f"Capacity = {capacity}")
    plt.scatter([14], [26], marker="*", s=180, label="Known optimum (14, 26)")
    plt.xlabel("Total weight")
    plt.ylabel("Total value")
    plt.title("O3 Knapsack Solution Landscape")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()