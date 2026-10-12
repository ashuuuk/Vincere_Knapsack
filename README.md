# QFF 2026 — PS-O3: Combinatorial 0/1 Knapsack

**Team:** Team Vincere  
**Track:** Quantum Optimization (QAOA / QUBO)  
**Phase 1 scope:** Processor A (5 physical qubits) and Processor B (9 physical qubits) only.

## Problem instance

- Values: `[10, 4, 7, 5, 8]`
- Weights: `[5, 3, 4, 2, 6]`
- Capacity: `15`
- Quantum algorithm: p=1 QAOA with a deterministic ideal-statevector grid search for `(gamma, beta)`.
- Classical baseline: exhaustive enumeration of all `2^5 = 32` item selections.

The exact constrained classical optimum for this instance is selecting items 1, 2, 3 and 4 in one-based indexing (bit string `11110` in item order x0..x4): total value 26 and total weight 14.

## Modeling note — read this before presenting results

The official challenge asks for a QUBO with a quadratic capacity penalty. This implementation uses the five item-selection qubits so the same logical problem fits Processor A and Processor B. Its minimized energy is

`E(x) = -value(x) + P * (weight(x) - W)^2 + L * (weight(x) - W)`

with `P=1` and `L=1`. The linear bias breaks the symmetry of the squared term around capacity. This is a penalty-model choice, not a universal guarantee that every instance's QUBO ground state equals the constrained knapsack optimum. The code therefore separately enumerates and reports the exact constrained optimum and the QUBO ground state. Discuss this distinction in the report and tune/justify penalty parameters if your experiments show a mismatch.

A textbook inequality-to-QUBO conversion can instead add binary slack variables; that requires more than five logical qubits for this instance and would not fit the 5-qubit Processor A without a reduced encoding. Do not claim that this repository implements a slack-variable encoding.

## Processor models

- `processors/processor_A.json`: 5 nodes, participant-defined branching topology.
- `processors/processor_B.json`: 9 nodes, 12-edge heavy-hex-inspired topology.
- Both use basis gates `{rz, sx, x, cx}` and the same synthetic noise rates: one-qubit depolarizing `0.001`, CX depolarizing `0.005`, readout error `0.01`.
- Transpilation uses optimization level 1 and seed 42. Noisy sampling uses 4096 shots per processor.

These are synthetic simulator models, not actual IBM Quantum hardware backends or hardware measurements.

## Repository layout

```text
PS-O3-Knapsack/
├── README.md
├── main.ipynb
├── requirements.txt
├── run_experiment.py
├── data/
│   ├── raw/
│   └── processed/
├── processors/
│   ├── processor_A.json
│   └── processor_B.json
├── src/
│   ├── __init__.py
│   ├── problem.py
│   ├── processors.py
│   ├── routing.py
│   ├── metrics.py
│   └── visualization.py
├── results/
│   ├── tables/
│   └── figures/
├── report.md
└── assets/qff_phase1_latex_images/
```

## Setup on macOS

Use Python 3.11 or 3.12 for the smoothest package compatibility. From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the full experiment:

```bash
python run_experiment.py
```

Or launch the notebook:

```bash
jupyter notebook main.ipynb
```

The run creates benchmark CSV/JSON files and PNG figures under `results/`.

## What is measured

- Logical circuit depth and CX-equivalent count.
- Transpiled circuit depth and CX count.
- Estimated routing-SWAP overhead, inferred from excess CX count (an estimate, not an exact count of SWAP instructions after basis decomposition).
- Feasible-shot rate, best feasible value observed, and hit rate for the known classical optimum.
- Coupling-map diagrams and a processor metric comparison plot.

## Reproducibility and limitations

- Fixed random seeds are used for transpilation and simulator sampling.
- The QAOA parameters are selected by a small deterministic grid search on an ideal statevector; the noisy Processor A/B circuits use the same parameters for a fair architecture comparison.
- The p=1 grid search is a baseline, not proof of a globally optimal QAOA parameter set.
- The physical graph and noise are synthetic assumptions. Report the coupling graph rationale and limitations.
- Run the notebook/script before submission so the CSV/JSON/PNG outputs are generated from your environment. Do not fabricate benchmark values.

## Submission checklist

- [ ] Review the official Drive instructions and confirm this is the team's selected problem statement.
- [ ] Run `python run_experiment.py` successfully.
- [ ] Inspect all generated tables and plots.
- [ ] Complete `report.md` with actual results, interpretation, limitations, and each team member's contribution.
- [ ] Push the project to a **public** GitHub repository.
- [ ] Submit the public repository URL at the official QFF submission portal.
