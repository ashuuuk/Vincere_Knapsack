# Vincere Knapsack — Quantum Optimization

**Qiskit Fall Fest 2026 | Quantum Optimization Track | PS-O3: Knapsack**

## About the Project

Vincere Knapsack explores the **Combinatorial 0/1 Knapsack Problem** using Qiskit and quantum optimization techniques.

The objective is to select a subset of items that maximizes total value while keeping the total weight within the knapsack capacity.

This project formulates the knapsack problem as a Quadratic Unconstrained Binary Optimization (QUBO) problem and applies the Quantum Approximate Optimization Algorithm (QAOA) to search for high-quality solutions. The results are compared against an exhaustive classical baseline to evaluate solution quality, feasibility, circuit resources, and processor configurations.

## Problem Definition

The Phase 2 challenge uses the official locked PS-O3 instance.

| Parameter | Value |
|---|---|
| Number of items | 5 |
| Knapsack capacity | 15 |
| Item values | 10, 4, 7, 5, 8 |
| Item weights | 5, 3, 4, 2, 6 |
| QAOA depth | \(p = 1\) for required runs |
| Reference penalty | \(P = 5\) |
| Logical qubits | 9 |
| Evaluation shots | 4096 per required sampled result |

The encoding uses five item-selection qubits and four binary slack-variable qubits. This produces the required nine-qubit QUBO formulation.

The classical optimum is calculated through exhaustive enumeration of all 32 possible item subsets. Feasibility is evaluated using the five item-selection bits, with total weight not exceeding 15.

## Repository Structure

```text
Vincere_Knapsack/
├── README.md
├── Phase1/
│   └── Phase 1 project materials
└── Phase2/
    ├── README.md
    ├── main.ipynb
    ├── requirements.txt
    ├── run_experiment.py
    ├── processors/
    ├── src/
    ├── data/
    ├── results/
    │   ├── tables/
    │   └── figures/
    └── report.md
```

- **`Phase1/`** — Phase 1 project materials.
- **`Phase2/main.ipynb`** — Main experiment notebook.
- **`Phase2/run_experiment.py`** — Experiment execution script.
- **`Phase2/requirements.txt`** — Python dependencies for the project.
- **`Phase2/processors/`** — Quantum processor configurations.
- **`Phase2/src/`** — Problem formulation, QUBO construction, optimization, and supporting modules.
- **`Phase2/data/`** — Problem instance data.
- **`Phase2/results/tables/`** — Experimental result tables.
- **`Phase2/results/figures/`** — Generated plots and figures.
- **`Phase2/report.md`** — Technical report and experimental analysis.
- **`Phase2/README.md`** — Phase 2 setup and execution instructions.

## Technologies Used

- Python
- Qiskit
- Qiskit Aer
- NumPy
- Matplotlib
- Jupyter Notebook

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ashuuuk/Vincere_Knapsack.git
cd Vincere_Knapsack/Phase2
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate the environment using:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the experiment notebook

Launch Jupyter Notebook:

```bash
jupyter notebook main.ipynb
```

Execute the notebook cells from top to bottom without modifying the required benchmark settings.

The notebook should reproduce the experiment results and figures documented in the repository.

## Experimental Methodology

The project evaluates the quantum optimization approach through the following steps:

1. **Problem formulation:** Encode the knapsack objective and capacity constraint into a nine-qubit QUBO using four binary slack variables and the reference penalty \(P = 5\).
2. **Classical baseline:** Enumerate all 32 item subsets to determine the exact optimal feasible value.
3. **Quantum optimization:** Apply QAOA with required depth \(p = 1\) and at least five initializations using the official seeds.
4. **Processor benchmarking:** Evaluate the required Processor B and Processor D configurations under ideal and noisy simulation. Processor A is reported as not executable because it has only five qubits.
5. **Solution evaluation:** Measure feasibility, best feasible value, percentage of optimal value, and optimal-solution sampling probability.
6. **Circuit analysis:** Compare CX counts, circuit depth, two-qubit depth, SWAP counts, and routing overhead.
7. **Objective landscape:** Evaluate the required noisy Processor D landscape using at least a 20 × 20 parameter grid and 1024 shots per grid point.
8. **Technical analysis:** Discuss the effects of noise, connectivity, feasibility, and circuit resources, including limitations and potential improvements.

Required benchmark runs use the official challenge-kit settings. Any additional experiments must be clearly labelled.

## Results and Reproducibility

The repository is intended to include the following evaluation artifacts:

- `results/tables/results.csv` — Main benchmark results in the official challenge-kit format.
- `results/tables/bell.csv` — Bell-state correlations, fidelity, and standard errors.
- `results/figures/` — Figures used in the technical report, including the required objective-landscape plot.
- `report.md` — Formulation, results, processor comparison, limitations, and proposed improvements.

The notebook must run from a clean environment, reproduce the reported results, and complete within the challenge kit's 30-minute CPU execution limit. Required result files must be committed to the repository.

## Evaluation Criteria

The project follows the Qiskit Fall Fest 2026 Phase 2 Quantum Optimization judging rubric:

- **Bell-state verification:** Correct Bell-state preparation, XX/YY/ZZ correlations, fidelity, and standard errors.
- **Processor D design:** Valid processor configuration, connectivity analysis, routing overhead, and justified design trade-offs.
- **Solution and benchmarking:** Correct QUBO formulation, classical optimum, quantum solution quality, feasibility, random-baseline comparison, and resource metrics.
- **Validation and reproducibility:** Required files, pinned dependencies, official settings, and reproducible notebook execution.
- **Technical analysis:** Evidence-based interpretation, limitations, figures, and concrete next improvements.

## Team

**Team Vincere**

**Problem statement:** PS-O3 — Knapsack

