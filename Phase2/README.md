# QFF 2026 — PS-O3: Combinatorial 0/1 Knapsack

**Team:** Team Vincere  
**Track:** Quantum Optimization (QAOA / QUBO)  
**Problem Statement:** PS-O3 — Resource-Constrained Item Selection (0/1 Knapsack)  
**Phase:** Phase 2

## 1. Project Overview

This project addresses the Combinatorial 0/1 Knapsack problem using Qiskit and quantum optimization techniques. The objective is to select a subset of items that maximizes total value without exceeding a given capacity.

The project compares quantum optimization results across different processor configurations, evaluates solution quality and feasibility, measures circuit resources, and investigates how processor topology and noise affect performance.

The Phase 2 implementation is intended to evaluate Processor A, Processor B, and a designed Processor D using a reproducible experimental workflow.

## 2. Problem Instance

The problem contains five items.

| Item | Value | Weight |
|---|---:|---:|
| 1 | 10 | 5 |
| 2 | 4 | 3 |
| 3 | 7 | 4 |
| 4 | 5 | 2 |
| 5 | 8 | 6 |

**Capacity:** 15

The objective is

\[
\max \sum_{i=1}^{5} v_i x_i
\]

subject to

\[
\sum_{i=1}^{5} w_i x_i \leq 15,
\qquad x_i \in \{0,1\}.
\]

Here, \(v_i\) is the value of item \(i\), \(w_i\) is its weight, and \(x_i=1\) means that the item is selected.

### Classical reference solution

The exact constrained optimum must be computed by exhaustively evaluating all \(2^5=32\) possible item selections.

For the specified instance, the optimal selection is items 1, 2, 3, and 4:

- **Item-selection bitstring:** `11110`, in the order \(x_0,x_1,x_2,x_3,x_4\).
- **Total value:** 26.
- **Total weight:** 14.
- **Capacity:** 15.

This classical optimum is the reference for evaluating the quantum results.

## 3. QUBO Formulation

The knapsack problem must be converted into a Quadratic Unconstrained Binary Optimization (QUBO) problem so it can be evaluated using QAOA.

The Phase 2 formulation requires **nine binary variables: five item-selection variables and four binary slack variables**, with penalty parameter \(P=5\).

The item-selection variables represent whether each item is included. The slack variables encode unused capacity so the capacity constraint can be incorporated into the unconstrained objective.

The QUBO objective combines the negative total item value with a quadratic penalty for violating the capacity constraint. The penalty discourages invalid solutions while allowing the optimizer to search over binary assignments.

The implementation must use the required nine-qubit formulation and the official penalty setting. Feasibility must be evaluated using the five item-selection bits and the original capacity constraint, rather than treating slack-bit assignments alone as proof of feasibility.

The exact constrained classical optimum must be computed independently and compared with the quantum results.

**Implementation note:** The original five-qubit implementation is a baseline and does not, by itself, satisfy the required nine-qubit Phase 2 formulation. Update this section if the implementation or official problem specification changes.

## 4. Quantum Optimization Approach

The project uses Qiskit to construct and evaluate quantum optimization circuits.

The experimental workflow is intended to include:

1. Formulate the knapsack problem as a QUBO.
2. Construct the corresponding cost Hamiltonian and QAOA circuit.
3. Evaluate the circuit using the specified simulator and processor configurations.
4. Transpile circuits to the target processor coupling maps.
5. Measure circuit resources and sampled solution distributions.
6. Calculate feasibility and solution-quality metrics.
7. Compare quantum results against the exhaustive classical reference and the required random baseline.

The QAOA depth, parameter-selection procedure, simulator settings, and random seeds must be documented and kept consistent with the official Phase 2 instructions.

## 5. Processor Configurations

### Processor A

Processor A is the five-qubit baseline processor configuration. It is useful for the baseline resource and topology analysis, but it cannot execute the required nine-qubit O3 formulation as a full nine-qubit circuit.

### Processor B

Processor B is the nine-qubit baseline processor configuration. It is used for the required O3 solution and benchmarking results.

### Processor D

Processor D is the participant-designed processor configuration for Phase 2. Its topology and noise assumptions must be documented and its configuration must pass the official `validate_processor_d()` validation.

The design analysis should explain the topology, identify relevant bottlenecks using measurements on Processors A and B, compare expected and measured effects, and discuss trade-offs honestly.

**Important:** Processor configurations and simulator noise models must not be described as real hardware measurements unless actual hardware experiments were performed. Any synthetic noise rates and topology assumptions must be explicitly identified as simulated assumptions.

## 6. Experimental Evaluation

The experiment should report the required metrics using the official project utilities and settings.

### Solution quality

- Exact constrained classical optimum.
- Best feasible value found by the quantum method.
- Feasible-shot probability, \(P_{\mathrm{feasible}}\).
- Optimal-value hit rate.
- Comparison with the specified random-selection baseline.
- Solution-distribution or objective-landscape visualization, with the optimum clearly marked.

### Circuit resources

- Logical circuit depth.
- Logical CX-equivalent count.
- Transpiled circuit depth.
- Transpiled CX count.
- Routing overhead, where supported by the official measurement procedure.
- Comparison of Processor A, Processor B, and Processor D wherever the relevant circuit is supported.

Circuit-resource measurements must be generated using the official `circuit_metrics()` procedure and reported with the required capacity rule. Do not invent measurements or report estimates as exact counts.

### Processor comparison

The report should compare the processor configurations in terms of circuit resources, solution quality, feasibility, topology, and noise. Any claim about improved performance must be supported by measured results.

## 7. Required Results and Artifacts

The Phase 2 submission must include the required reproducible experiment and result files.

Expected deliverables include:

- `main.ipynb` — the notebook used to run and demonstrate the experiment.
- `requirements.txt` — Python dependencies, pinned as required for reproducibility.
- `processors/processor_A.json` — Processor A configuration.
- `processors/processor_B.json` — Processor B configuration.
- `processors/processor_D.json` — designed Processor D configuration.
- `results/tables/results.csv` — benchmark results in the official kit format.
- `results/` — additional required tables, figures, and experiment outputs.
- `report.md` — technical report documenting the formulation, methodology, results, analysis, limitations, and team contributions.
- Supporting source code and data files required to reproduce the experiment.

Only list files as completed deliverables once they actually exist and have been verified.

## 8. Repository Structure

The project directory is expected to contain the following files and folders, along with any additional files used by the implementation:

```text
Phase2/
├── README.md
├── main.ipynb
├── requirements.txt
├── run_experiment.py
├── processors/
│   ├── processor_A.json
│   ├── processor_B.json
│   └── processor_D.json
├── src/
│   ├── __init__.py
│   ├── problem.py
│   ├── processors.py
│   ├── routing.py
│   ├── metrics.py
│   └── visualization.py
├── data/
│   ├── raw/
│   └── processed/
├── results/
│   ├── tables/
│   │   └── results.csv
│   └── figures/
└── report.md
```

The exact structure should match the actual repository. Remove any entries that do not exist and add any required project files that are missing.

## 9. Setup on macOS

Use Python 3.11 or 3.12 if supported by the pinned dependencies.

Open Terminal and navigate to the Phase 2 project directory:

```bash
cd Phase2
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Upgrade pip and install the dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Run the experiment

If the experiment script is present and configured for the required Phase 2 workflow:

```bash
python run_experiment.py
```

### Launch the notebook

```bash
jupyter notebook main.ipynb
```

Run the notebook from beginning to end in the configured environment. Confirm that it generates the required Processor B results and all required output files. Follow the official Phase 2 instructions if they specify a different execution procedure.

## 10. Reproducibility

The project should document and maintain:

- Python and dependency versions.
- Random seeds used for circuit generation, transpilation, and simulator sampling.
- QAOA depth and parameter-selection procedure.
- Official processor configurations and experiment settings.
- The procedure used to calculate the exact constrained optimum.
- Commands required to reproduce the experiment.
- The output files generated by each run.

Results must be generated from the actual implementation. Do not fabricate benchmark values, substitute illustrative numbers for experimental results, or claim successful validation without running the relevant checks.

A clean-clone test should verify that another person can follow the README and reproduce the required results without manually editing the code.

## 11. Technical Report

The accompanying `report.md` should explain:

1. The problem statement and mathematical formulation.
2. The nine-qubit QUBO, slack-variable encoding, and penalty parameter.
3. The classical reference solution and the method used to obtain it.
4. The experimental setup and QAOA parameter-selection procedure.
5. Solution feasibility and quality compared with the random baseline.
6. The required objective-landscape or solution-distribution analysis.
7. Circuit-resource comparisons across the supported processor configurations.
8. Processor D topology, bottlenecks, expected effects, and measured trade-offs.
9. The limitations of the simulator, noise model, and optimization approach.
10. Reproducibility details, future improvements, and individual team contributions.

Include figures and tables generated from actual runs and explain what the results demonstrate.

## 12. Phase 2 Submission Checklist

- [ ] Confirm PS-O3 as the selected problem statement.
- [ ] Implement and verify the required nine-qubit QUBO with four slack bits and \(P=5\).
- [ ] Verify that feasibility is evaluated using the item-selection bits and original capacity constraint.
- [ ] Compute the exact constrained classical optimum using all 32 item selections.
- [ ] Run `main.ipynb` successfully and verify the required Processor B results.
- [ ] Implement `processors/processor_D.json` and validate it using `validate_processor_d()`.
- [ ] Measure the required circuit metrics using `circuit_metrics()`.
- [ ] Generate `results/tables/results.csv` in the official kit format.
- [ ] Generate the required tables and figures.
- [ ] Complete `report.md` with real measurements, interpretation, limitations, and team contributions.
- [ ] Pin dependencies and document reproducible execution steps.
- [ ] Test the workflow from a clean clone.
- [ ] Ensure the public GitHub repository contains all required deliverables.
- [ ] Submit the repository URL through the official QFF submission portal.

## 13. Limitations

Quantum optimization results depend on the QUBO formulation, penalty strength, QAOA depth, parameter selection, circuit compilation, processor connectivity, and noise assumptions.

Simulated results do not establish a quantum advantage over classical optimization. The exhaustive classical solution provides a reference for this small five-item instance, while the processor comparison helps investigate the effects of circuit resources and topology under the specified experimental conditions.

The report should distinguish theoretical expectations, simulated results, measured metrics, and limitations clearly.
