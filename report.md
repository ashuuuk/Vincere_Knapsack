# PS-O3 Architecture and Results Report

## 1. Objective
Implement a p=1 QAOA baseline for the QFF 2026 0/1 knapsack instance, verify it against exhaustive classical enumeration, and compare transpilation and synthetic-noise sampling on Processor A and Processor B.

## 2. Formulation
The item variables are binary. The QUBO penalty objective is documented in `README.md` and `src/problem.py`. The code separately computes the exact constrained knapsack optimum; compare it with the QUBO ground state before drawing conclusions.

## 3. Processor architecture rationale
- **Processor A:** 5-node branching graph `[(0,1),(1,2),(1,3),(3,4)]`. This graph has limited connectivity and can require routing for non-neighbor interactions.
- **Processor B:** 9-node, 12-edge heavy-hex-inspired graph specified in `processors/processor_B.json`. The larger and more connected topology gives the transpiler more placement/routing options.
- Both use identical synthetic noise rates to isolate connectivity and compilation effects as far as this simplified model allows.

## 4. Results
Run `python run_experiment.py`, then insert and interpret the actual outputs from:
- `results/tables/processor_metrics.csv`
- `results/tables/sampled_results.csv`
- `results/tables/benchmark_summary.json`
- `results/figures/processor_comparison.png`

Do not write numerical conclusions until the experiment has run.

## 5. Interpretation prompts
1. Which processor had lower transpiled depth and CX count? Why?
2. Did either processor have a higher feasible-shot rate or known-optimum hit rate?
3. Did the topology with more physical qubits perform better despite the same synthetic per-gate error rates?
4. How sensitive is the result to penalty parameters and QAOA grid resolution?
5. What changes would be needed for a strict slack-variable QUBO formulation?

## 6. Limitations
This is a small p=1 simulation, uses synthetic processor graphs/noise, and estimates routing SWAPs from excess CX count. It is not a real-device benchmark. The quadratic penalty is parameter-dependent; the exact constrained classical optimum is reported separately.
