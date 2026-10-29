
# PS-O3: Architecture, Optimization, and Results Analysis

**Event:** Qiskit Fall Fest 2026  
**Track:** Quantum Optimization  
**Problem Statement:** PS-O3 — Combinatorial 0/1 Knapsack  
**Team:** Team Vincere

## 1. Objective

This project investigates the use of the Quantum Approximate Optimization Algorithm (QAOA) for a five-item 0/1 knapsack problem. The study evaluates solution feasibility, objective quality, circuit resources, processor connectivity, and the effects of simulated noise.

The required formulation uses five item-selection variables and four binary slack variables, for a total of nine qubits. The penalty parameter is P = 5. Processor B is used as the nine-qubit baseline, and Processor D is evaluated as the participant-designed architecture. Processor A has only five physical qubits and is therefore not used to execute the complete nine-qubit circuit in the experiment reported here.

The experiments use Qiskit Aer simulations with synthetic noise. The measurements reported here are simulation results, not measurements from physical quantum hardware.

## 2. Problem Definition and Classical Reference

The instance contains five items:

| Item | Value | Weight |
|---|---:|---:|
| 1 | 10 | 5 |
| 2 | 4 | 3 |
| 3 | 7 | 4 |
| 4 | 5 | 2 |
| 5 | 8 | 6 |

The capacity is W = 15. Let x_i be a binary variable indicating whether item i is selected. The objective is

max V(x) = sum_i v_i x_i

subject to

sum_i w_i x_i <= 15.

Exhaustive enumeration of all 2^5 = 32 item selections gives the exact constrained optimum:

| Reference metric | Result |
|---|---:|
| Number of item selections | 32 |
| Optimal value | 26 |
| Weight of optimal selection | 14 |
| Capacity | 15 |
| Optimal item-selection bitstring | `11110` |

The bitstring is ordered by item index. It selects the first four items and excludes the fifth. Its total value is 10 + 4 + 7 + 5 = 26, and its total weight is 5 + 3 + 4 + 2 = 14.

This exact classical solution is used as the reference for evaluating sampled candidates. Feasibility is determined from the item bits, independently of the slack-bit assignment.

## 3. QUBO Formulation

The constrained problem is encoded as a quadratic unconstrained binary optimization problem with five item bits and four slack bits. The slack weights are 1, 2, 4, and 8, giving nine binary variables.

The implemented energy function is

E(x,s) = -V(x) + P (sum_i w_i x_i + sum_j 2^j s_j - W)^2,

where P = 5 and W = 15.

The item-value term rewards valuable selections, while the penalty term encourages the combined item weight and slack value to equal the capacity. Slack variables represent unused capacity; they are not additional items.

The classical exhaustive search reports a QUBO ground energy of -26.0, with the ground-state assignment `111101000` in the implementation's item-then-slack bit ordering. Its item bits are `11110`, and its slack bits represent 1 unit of unused capacity.

The exact constrained optimum and the QUBO ground state are checked separately. This distinction matters because the correctness of a penalty encoding depends on its coefficients and the resulting energy landscape.

## 4. Experimental Methodology

### 4.1 QAOA and parameter selection

The experiment constructs a p = 1 QAOA circuit over the nine QUBO variables. The circuit prepares an equal superposition, applies the cost unitary derived from the QUBO coefficients, applies an RX mixer, and measures all nine qubits.

The parameters gamma and beta are selected using an ideal statevector grid search with 13 gamma values and 13 beta values. The selected parameters are then used for noisy simulation on Processors B and D.

The recorded run returned:

| Parameter | Value |
|---|---:|
| QAOA depth p | 1 |
| Gamma | 0.3076327211 |
| Beta | 0.8103981634 |
| Grid points | 20 x 20 (400 points) |
| Shots per processor | 4096 |
| Transpiler optimization level | 1 |
| Transpiler seed | 42 |
| Simulator seed | 42 |

The reported grid-search expected QUBO energy was 172.9960. This is substantially above the exact ground energy of -26.0 and indicates that the current parameter search did not find a low-energy state. The value is retained as an observed output and should not be interpreted as evidence of successful QAOA optimization.

### 4.2 Processor configurations

Processor B uses a nine-qubit coupling map with 12 directed edges in its configuration. Processor D uses nine qubits and 18 configured edges. Processor D's design provides additional routing alternatives.

Processor A has five qubits, fewer than the nine required by the complete formulation. The full circuit was therefore not executed on Processor A in this run.

### 4.3 Noise and sampling

The simulations use Qiskit Aer with synthetic depolarizing errors for single-qubit and CX gates, plus a symmetric readout-error model. The configured rates are 0.001 for single-qubit depolarizing error, 0.005 for CX depolarizing error, and 0.01 for readout error.

These values are simulation assumptions. They are not validated physical-device calibration data, and the results must not be presented as actual hardware performance.

### 4.4 Random-selection baseline

A reproducible uniform random baseline independently samples five item-selection bits, using 4096 samples and random seed 42. Each selection is evaluated against the original capacity constraint.

This is the project's current exploratory baseline. It should be checked against the competition's prescribed random-selection procedure before being treated as the official benchmark.

## 5. Results and Benchmarking

### 5.1 Circuit resources

The latest experiment produced the following circuit metrics:

| Metric | Processor B | Processor D |
|---|---:|---:|
| Physical qubits in configuration | 9 | 9 |
| Logical circuit depth | 18 | 18 |
| Transpiled circuit depth | 316 | 227 |
| Logical CX-equivalent count | 72 | 72 |
| Transpiled CX count | 114 | 98 |
| Estimated routing swaps | 14.00 | 8.67 |
| Transpiled operation count | 616 | 493 |

Processor D had 89 fewer transpiled depth layers than Processor B, a reduction of approximately 28.2%. It also used 16 fewer transpiled CX gates, a reduction of approximately 14.0%, and had a lower estimated routing-swap count.

These results suggest that Processor D's configured connectivity reduces compilation overhead for this circuit under the current transpilation settings. They do not, by themselves, establish a general advantage across other circuits or hardware devices.

The routing-swap quantity is an estimate derived from the difference between physical CX count and logical CX-equivalent count. It is not a direct count of SWAP instructions and should be interpreted as a proxy.

### 5.2 Solution quality and feasibility

The measured noisy-simulation results were:

| Metric | Processor B | Processor D |
|---|---:|---:|
| Shots | 4096 | 4096 |
| Feasible-shot probability | 0.917969 (91.80%) | 0.918213 (91.82%) |
| Best feasible sampled value | 26 | 26 |
| Optimal-value hit rate | 0.015869 (1.59%) | 0.013916 (1.39%) |
| Most common item bits | `01101` | `01101` |
| Most common value | 19 | 19 |
| Most common weight | 13 | 13 |
| Mean feasible value | 14.2375 | 14.3209 |

Both processors sampled the exact optimal value of 26 at least once. However, the optimal-value hit rate was low, and the most frequently sampled item selection was `01101`, with value 19 and weight 13.

Processor D's feasible-shot probability was only marginally higher than Processor B's. Its mean feasible value was also slightly higher, but its optimal-value hit rate was lower. Consequently, the current sample does not demonstrate that Processor D produces the optimum more frequently than Processor B.

### 5.3 Uniform random-selection baseline

The uniform random baseline returned:

| Metric | Result |
|---|---:|
| Samples | 4096 |
| Feasible-shot probability | 0.879395 (87.94%) |
| Best feasible sampled value | 26 |
| Optimal-value hit rate | 0.030762 (3.08%) |
| Mean feasible value | 15.0811 |
| Random seed | 42 |

Compared with this baseline, Processor B had a higher feasible-shot probability but a lower optimal-value hit rate and lower mean feasible value. Processor D also had a higher feasible-shot probability but a lower optimal-value hit rate; its mean feasible value was lower than the random baseline as well.

The results therefore do not establish a solution-quality advantage over uniform random selection. The best sampled value of 26 alone is insufficient to show superiority, because the random baseline also sampled that value.

### 5.4 Interpretation

The resource metrics favor Processor D for this particular circuit and transpilation configuration. However, the sampling metrics do not show a corresponding improvement in optimal-value hit rate.

The current QAOA parameter selection is a major limitation: the grid search returned an expected energy of approximately 172.996, far above the known ground energy of -26.0. Further debugging and validation of the QUBO-to-Ising conversion, statevector energy evaluation, and parameter-selection procedure are necessary before drawing strong conclusions about QAOA solution quality.

The reported results should therefore be interpreted as an initial simulation benchmark, not as evidence of quantum advantage.

## 6. Limitations

1. **Parameter-selection quality:** The current grid search returned a high expected QUBO energy relative to the exact ground energy. The parameter-selection and energy-evaluation pipeline needs further validation.

2. **Synthetic noise:** The noise model uses fixed configured rates rather than validated device calibration data. The results are not physical hardware measurements.

3. **Processor A scope:** Processor A has only five qubits and was not used to run the complete nine-qubit formulation. A full nine-qubit comparison against Processor A is not available from this experiment.

4. **Random baseline definition:** The implemented baseline uniformly samples the five item bits. The competition's official baseline procedure must be verified before this result is considered compliant with the required benchmark.

5. **Circuit-resource estimates:** The routing-swap figure is an estimate, not a direct SWAP count. It should be labeled accordingly.

6. **Deliverable status:** The objective-landscape figure is saved at `results/figures/o3_solution_landscape.png`, and the official-format `results.csv` is saved at `results/tables/results.csv`. The local audit confirmed a 20 x 20 grid with 1024 shots per point and five rows in the official CSV. These files should remain synchronized with the experiment code and be checked again after regeneration.

7. **Statistical variability:** The experiment uses one configured seed and 4096 shots per processor. Repeated seeds or additional sampling would be needed to assess the stability of small differences in solution-quality metrics.

## 7. Reproducibility

The experiment is run from the Phase 2 directory with the project's Python environment activated:

```bash
python -m src.problem
python run_experiment.py
```

The recorded environment uses Qiskit 2.2.3 and Qiskit Aer 0.17.2 in Python 3.12.16. The latest landscape uses a 20-by-20 parameter grid with 1024 shots per point. Processor-condition simulations use 4096 shots, transpiler optimization level 1, transpiler seed 42, and simulator seed 42.

The generated outputs include:

- `results/tables/processor_metrics.csv`
- `results/tables/sampled_results.csv`
- `results/tables/random_baseline.csv`
- `results/tables/benchmark_summary.json`
- `results/tables/processor_B_counts.csv`
- `results/tables/processor_D_counts.csv`
- `results/figures/processor_B_coupling.png`
- `results/figures/processor_D_coupling.png`
- `results/figures/processor_comparison.png`

The saved tables and figures should be regenerated whenever the experiment code, parameter-selection procedure, processor topology, or noise assumptions change.

## 8. Conclusion

The exact classical optimum for the five-item instance has value 26 at weight 14, with item-selection bits `11110`. The nine-qubit QUBO encoding uses five item variables, four slack variables, and penalty P = 5.

In the current noisy simulations, both Processor B and Processor D sampled the optimal value. Processor D had lower transpiled circuit depth and fewer transpiled CX gates, indicating lower compilation overhead for this circuit under the configured topology and transpilation settings.

However, neither quantum simulation outperformed the implemented uniform random baseline in optimal-value hit rate. The high expected energy returned by the parameter grid search also indicates that the QAOA optimization pipeline needs further validation.

The strongest supported conclusion is that Processor D shows a promising circuit-resource advantage in this simulation, while a solution-quality advantage has not been demonstrated. The official baseline, objective-landscape visualization, and required results-file format must be validated before the submission can be considered complete.
