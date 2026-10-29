# PS-O3: Architecture, Optimization, and Results Analysis

**Event:** Qiskit Fall Fest 2026  
**Track:** Quantum Optimization  
**Problem Statement:** PS-O3 — Combinatorial 0/1 Knapsack  
**Team:** Team Vincere

## 1. Objective

This project evaluates a depth-one Quantum Approximate Optimization Algorithm (QAOA) approach to a five-item 0/1 knapsack problem. The work covers the mathematical formulation, exact classical reference, QAOA parameter selection, circuit compilation, processor connectivity, simulated noise, Bell-state verification, and solution-quality benchmarking.

The QUBO formulation uses five item-selection variables and four binary slack variables, requiring nine qubits. The penalty coefficient is \(P=5\). Processor B provides the baseline nine-qubit topology, while Processor D is the team-designed architecture. Processor A has five physical qubits and cannot execute the complete nine-qubit formulation.

All reported processor results are local simulations with configured synthetic noise, not measurements from physical quantum hardware.

## 2. Problem Definition and Classical Reference

The knapsack instance contains five items.

| Item | Value | Weight |
|---|---:|---:|
| 1 | 10 | 5 |
| 2 | 4 | 3 |
| 3 | 7 | 4 |
| 4 | 5 | 2 |
| 5 | 8 | 6 |

The capacity is \(W=15\). Let \(x_i\in\{0,1\}\) indicate whether item \(i\) is selected. The objective is to maximize

\[
V(x)=\sum_i v_i x_i
\]

subject to

\[
\sum_i w_i x_i\leq 15.
\]

Exhaustive enumeration of all 32 possible item selections gives the following exact constrained optimum.

| Metric | Result |
|---|---:|
| Number of item selections | 32 |
| Optimal value | 26 |
| Weight of optimal selection | 14 |
| Unused capacity | 1 |
| Optimal item bitstring | `11110` |

The bitstring selects the first four items and excludes the fifth. Its value is \(10+4+7+5=26\), and its weight is \(5+3+4+2=14\).

This exhaustive solution is the classical reference for the sampled QAOA candidates. Feasibility is evaluated using the five item bits and the original capacity constraint, rather than inferred from the slack bits alone.

## 3. QUBO Formulation

The implementation encodes the problem using five item bits and four slack bits with weights 1, 2, 4, and 8. The resulting nine-variable energy function is

\[
E(x,s)=-\sum_i v_i x_i+
P\left(\sum_i w_i x_i+\sum_j 2^j s_j-W\right)^2,
\]

where \(P=5\), \(W=15\), and each \(s_j\) is binary.

The negative value term rewards valuable item selections. The quadratic penalty encourages the item weight plus the slack value to equal the capacity. The slack variables represent unused capacity and are not additional items.

The exact classical reference reports a QUBO ground energy of \(-26.0\). The ground-state assignment in item-then-slack ordering is `111101000`, corresponding to item bits `11110` and slack bits representing one unit of unused capacity.

The constrained optimum and QUBO ground state are checked independently. A good feasible item selection does not automatically imply that the full item-plus-slack bitstring has low QUBO energy.

## 4. Experimental Methodology

### 4.1 QAOA and parameter selection

The QAOA circuit uses \(p=1\). It prepares a uniform superposition, applies the QUBO-derived cost unitary, applies an RX mixer, and measures the nine qubits.

Parameter selection uses five seeded local-grid searches, with seeds 0 through 4, alongside a separate global grid search. The selected parameters from the latest experiment are:

| Parameter | Value |
|---|---:|
| QAOA depth \(p\) | 1 |
| Gamma | 2.617993877991494 |
| Beta | 0.7853981633974483 |
| Expected QUBO energy | 116.56020144 |
| Seeded starts | 5 |
| Grid steps per dimension | 25 |
| Processor-condition shots | 4096 |

The selected parameters are recorded in `data/processed/qaoa_optimization.json` and are used consistently for the processor simulations, result metadata, and landscape marker.

The expected QUBO energy is substantially above the exact ground energy of \(-26.0\). Therefore, the selected parameters do not establish that the QAOA state is close to the QUBO ground state. Item-level feasibility and optimal-value hit rate must be interpreted separately from the expected energy of the complete nine-bit assignment.

### 4.2 Processor configurations

Processor B uses nine qubits and a configured coupling map. Processor D uses nine qubits and an 18-edge topology with additional routing alternatives. The Processor D design is connected and has maximum degree four.

Processor D's configuration uses the required basis gates `rz`, `sx`, `x`, and `cx`, with the configured synthetic noise rates:

- Single-qubit depolarizing probability: 0.001
- CX depolarizing probability: 0.005
- Readout error probability: 0.01

The topology is evaluated by transpiling the same logical circuit and comparing circuit resources and sampled quality. Connectivity alone does not guarantee better results: routing, circuit depth, and accumulated noise must also be considered.

Processor A has five qubits, fewer than the nine required. It is recorded as non-executable for this problem rather than being used for an incomplete comparison.

### 4.3 Noise and sampling

The ideal and noisy conditions are simulated with Qiskit Aer. Each executable processor-condition experiment uses 4096 shots. Official transpilation uses optimization level 1 and seed 42, and the simulator seed is 42.

The noise model is synthetic and uses fixed error probabilities. These probabilities are assumptions for controlled simulation, not physical-device calibration data.

### 4.4 Uniform random-selection baseline

The exact uniform baseline enumerates all 32 item selections. Under uniform sampling, the probability of selecting a feasible subset is \(28/32=0.875\). The probability of selecting the unique optimal item subset is \(1/32=0.03125\).

This exact baseline is useful for interpreting the measured QAOA results. A feasible-shot rate above 0.875 indicates more frequent feasible item selections than uniform random selection, while an optimal-value hit rate above 0.03125 indicates more frequent sampling of the optimal item value.

## 5. Results and Benchmarking

### 5.1 Circuit resources

The latest official transpilation results are:

| Metric | Processor B | Processor D |
|---|---:|---:|
| Logical qubits | 9 | 9 |
| Physical qubits | 9 | 9 |
| Logical CX count | 56 | 56 |
| Transpiled CX count | 98 | 82 |
| Transpiled circuit depth | 101 | 78 |
| Two-qubit depth | 74 | 57 |
| Actual routing SWAP count | 14 | 10 |
| CX overhead | 42 | 26 |

Processor D reduces transpiled circuit depth from 101 to 78, a reduction of approximately 22.8%. Its CX count decreases from 98 to 82, a reduction of approximately 16.3%. The actual routing SWAP count decreases from 14 to 10, a reduction of approximately 28.6%.

The CX overhead is defined as the transpiled CX count minus the logical CX count. Processor B has an overhead of \(98-56=42\), while Processor D has an overhead of \(82-56=26\).

These results support a circuit-resource advantage for Processor D under the tested topology and official transpilation settings. The SWAP figures are actual routing SWAP counts from the official metric implementation, not estimates inferred from CX overhead. These comparisons do not establish a general advantage on other circuits or real hardware.

### 5.2 Solution quality and feasibility

The official-format results table reports the following metrics. `quality_value` is the feasible-shot rate, and `p_opt` is the optimal-value hit rate.

| Processor | Condition | Shots | Feasible-shot rate | Optimal-value hit rate |
|---|---|---:|---:|---:|
| B | Ideal | 4096 | 0.978516 | 0.015625 |
| B | Noisy | 4096 | 0.970459 | 0.029297 |
| D | Ideal | 4096 | 0.983887 | 0.013672 |
| D | Noisy | 4096 | 0.968506 | 0.023682 |
| A | Not executable | 0 | N/A | N/A |

The classical optimum value is 26. Both executable processors sampled the optimal value under ideal and noisy conditions, although the optimal-value hit rates were low.

Under noisy simulation, Processor B has an optimal-value hit rate of 0.029297, compared with 0.023682 for Processor D. Processor B also has a slightly higher feasible-shot rate, 0.970459 compared with 0.968506 for Processor D.

The ideal-to-noisy comparison shows that noise reduces the feasible-shot rate on both processors. The optimal-value hit rate does not decrease uniformly in the sampled results: it increases from 0.015625 to 0.029297 for B and from 0.013672 to 0.023682 for D. These are finite-shot observations, not evidence that adding noise improves QAOA in general.

Processor D has fewer compiled CX gates, lower depth, and fewer routing SWAPs, but Processor B performs slightly better on both reported noisy item-level quality metrics. The evidence therefore supports a resource advantage for D, not universal superiority across every metric.

### 5.3 Uniform random-selection baseline

The exact uniform random baseline gives:

| Metric | Result |
|---|---:|
| Feasible-selection probability | 0.875 |
| Optimal-value probability | 0.03125 |
| Number of subsets | 32 |
| Classical optimum value | 26 |

Both processors' noisy feasible-shot rates exceed the uniform baseline of 0.875. However, the noisy optimal-value hit rates of both processors are below the exact uniform baseline probability of 0.03125 in this run.

These comparisons should be interpreted carefully. The random baseline is defined over the five item bits, whereas QAOA samples nine bits including slack variables. The quality metrics compare the resulting item selections against the original knapsack constraint; they do not mean that the complete QUBO assignment is near its ground state. The high selected expected QUBO energy reinforces the need to distinguish item-level solution quality from full-QUBO energy.

### 5.4 Bell-state verification

Bell-state verification is performed on Processor D for an adjacent pair, (0, 1), at configured distance 1, and a farther pair, (0, 6), at configured distance 3. For each pair, the experiment measures XX, YY, and ZZ correlations under ideal and configured noisy simulation, using 4096 shots per measurement basis.

The Bell fidelity is calculated from all three correlations:

\[
F=\frac{1+\langle XX\rangle-\langle YY\rangle+\langle ZZ\rangle}{4}.
\]

The fidelity standard error is propagated from the standard errors of the three correlation estimates.

| Pair | Condition | XX | YY | ZZ | Fidelity ± SE |
|---|---|---:|---:|---:|---:|
| Adjacent (0, 1) | Ideal | 1.000000 | -1.000000 | 1.000000 | 1.000000 ± 0.000000 |
| Adjacent (0, 1) | Noisy | 0.943359 | -0.947754 | 0.959961 | 0.962769 ± 0.002105 |
| Farthest (0, 6) | Ideal | 1.000000 | -1.000000 | 1.000000 | 1.000000 ± 0.000000 |
| Farthest (0, 6) | Noisy | 0.915039 | -0.903809 | 0.924316 | 0.935791 ± 0.002738 |

The ideal simulations produce the expected Bell correlations and unit fidelity for both pairs. Under configured noise, the adjacent pair has higher fidelity than the farther pair. The farther pair also has a larger propagated standard error in this run.

This is consistent with a possible cost from additional routing and gate exposure for the farther pair. It is not proof that distance alone causes the difference: the results depend on transpilation, the coupling map, noise placement, and the sampled measurements. The noisy Bell results are simulated observations, not hardware measurements.

The CSV stores one row per pair, condition, and measurement basis. The same combined fidelity is repeated on the three basis rows for a given pair and condition; it is not a separate fidelity estimate from each basis alone.

### 5.5 Processor D landscape

The saved Processor D landscape uses a 20 × 20 grid over beta in \([0,\pi]\) and gamma in \([0,\pi]\), with 1024 shots per grid point. The plot shows sampled mean QUBO cost across the parameter grid and marks the selected parameters:

- Gamma: 2.617993877991494
- Beta: 0.7853981633974483

The landscape metadata and result metadata use the same selected parameter pair.

A landscape helps show the variation in the sampled objective with QAOA parameters. Because the plotted costs are finite-shot estimates under the configured simulation, local fluctuations are possible. The selected parameters should be interpreted alongside the classical ground energy and item-level sampling metrics rather than as evidence of successful ground-state preparation by themselves.

## 6. Limitations and Improvements

1. **QUBO energy remains high.** The selected expected energy is 116.56020144, compared with the exact ground energy of -26.0. The parameter search and resulting state have not reached a low-energy regime. Further work should investigate parameter-grid resolution, cost-unitary scaling, and the relationship between sampled item feasibility and slack-variable penalties.

2. **Synthetic noise only.** The fixed error probabilities simplify comparison but do not model a calibrated physical device. Results should not be presented as real-hardware performance.

3. **Processor A cannot execute the full problem.** Its five-qubit capacity is smaller than the nine-qubit encoding. Its non-executable row must remain explicit rather than being treated as a failed quality result.

4. **Resource metrics depend on compilation.** The official metrics are specific to the selected circuit, processor coupling map, optimization level, and transpiler seed. Different circuits or settings may produce different results.

5. **Sampling uncertainty.** Each processor-condition run uses 4096 shots. Small differences between B and D should not be overinterpreted without repeated seeds or uncertainty analysis.

6. **Bell-pair comparison is topology-dependent.** The difference between adjacent and farther-pair fidelity may reflect routing and gate exposure, but the experiment does not isolate distance as the only causal factor.

7. **Baseline interpretation.** The exact random baseline is defined over item selections. Comparisons should continue to use the same feasibility and optimal-value definitions and should clearly distinguish the five item bits from the four slack bits.

Concrete next improvements are to evaluate a finer or scaled parameter search, report the distribution of feasible item values and full QUBO energies separately, repeat processor simulations across multiple simulator seeds, and inspect the transpiled circuits to measure actual routing operations. These steps would strengthen the conclusions without claiming quantum advantage.

## 7. Reproducibility

The experiment is run from the Phase 2 project directory. The key generated artifacts include:

- `data/processed/qaoa_optimization.json`
- `data/processed/landscape_metadata.json`
- `results/tables/results.csv`
- `results/tables/benchmark_summary.json`
- `results/tables/processor_metrics.csv`
- `results/tables/sampled_results.csv`
- `results/tables/bell.csv`
- `results/figures/o3_solution_landscape.png`
- `results/figures/processor_comparison.png`
- `results/figures/processor_D_coupling.png`
- `main.ipynb`

The official results table contains five rows: ideal and noisy results for B and D, plus a non-executable row for A. The Bell table contains 12 rows covering two pairs, two noise conditions, and three measurement bases.

The notebook and report should be kept synchronized with the code and generated outputs. A clean top-to-bottom notebook run should be tested before submission. The dependency versions and random seeds used by the experiment should be retained in the repository.

## 8. Conclusion

The exact classical optimum for this instance has value 26 and weight 14, with item-selection bits `11110`. The QAOA experiment uses a nine-qubit item-plus-slack encoding and \(p=1\).

Processor D demonstrates a clear circuit-resource improvement over Processor B in the current official compilation results: lower transpiled depth, fewer CX gates, fewer routing SWAPs, and lower CX overhead. In noisy sampling, Processor B has a slightly higher optimal-value hit rate and feasible-shot rate. Both processors exceed the uniform random baseline on feasible-shot rate, but neither exceeds the uniform baseline's optimal-value hit probability in this run.

Bell-state simulations show ideal fidelity of 1.0 for both tested pairs. Under configured synthetic noise, the adjacent pair's fidelity is higher than the farther pair's, consistent with a possible routing-related cost.

However, the selected expected QUBO energy remains far above the exact ground energy. The results support a topology-related resource improvement, but the item-level quality metrics do not demonstrate consistent improvement over uniform random selection in finding the optimal value. They do not demonstrate quantum advantage or successful preparation of a low-energy QUBO ground state. Further parameter and energy-landscape validation is needed before making stronger claims.
