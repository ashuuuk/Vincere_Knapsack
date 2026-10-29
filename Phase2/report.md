# PS-O3: Architecture, Optimization, and Results Analysis

**Event:** Qiskit Fall Fest 2026  
**Track:** Quantum Optimization  
**Problem Statement:** PS-O3 — Combinatorial 0/1 Knapsack  
**Team:** Team Vincere

## 1. Objective

The objective of this project is to investigate the use of the Quantum Approximate Optimization Algorithm (QAOA) for solving the Combinatorial 0/1 Knapsack problem. The study evaluates solution feasibility, objective quality, circuit resources, processor connectivity, and the effects of simulated noise.

The experimental analysis compares quantum optimization results with an exact classical reference and the prescribed random baseline. It also investigates how processor architecture and circuit compilation affect the measured output distribution.

The Phase 2 evaluation must use the official nine-qubit O3 formulation, including five item-selection variables, four slack variables, and penalty parameter \(P=5\). Processor B is the required baseline for the scored O3 solution results, while Processor D is evaluated as the participant-designed architecture. Processor A is used for the applicable baseline and architecture analysis.

**Implementation status:** The existing five-qubit p=1 implementation provides a baseline for the analysis described below. Results from that implementation must not be presented as results from the required nine-qubit Phase 2 formulation unless the formulation has actually been implemented and verified.

## 2. Problem Definition and Classical Reference

The knapsack problem consists of five items with the following values and weights.

| Item | Value | Weight |
|---|---:|---:|
| 1 | 10 | 5 |
| 2 | 4 | 3 |
| 3 | 7 | 4 |
| 4 | 5 | 2 |
| 5 | 8 | 6 |

The knapsack capacity is \(W=15\).

Let \(x_i\in\{0,1\}\) indicate whether item \(i\) is selected. The constrained optimization problem is

\[
\max V(x)=\sum_{i=1}^{5}v_i x_i
\]

subject to

\[
\sum_{i=1}^{5}w_i x_i\leq 15.
\]

The exact classical solution is obtained by exhaustive enumeration of all \(2^5=32\) item selections.

For this instance, the optimal selection is `11110`, in the order \(x_0,x_1,x_2,x_3,x_4\). It selects the first four items, producing a total value of 26 and total weight of 14.

| Reference metric | Value |
|---|---:|
| Number of item selections | 32 |
| Optimal feasible value | 26 |
| Weight of optimal selection | 14 |
| Capacity | 15 |
| Optimal item-selection bitstring | `11110` |

This classical solution provides the reference for assessing the quality of quantum-generated candidates. Feasibility and objective quality are evaluated separately: a high-value candidate is not a valid solution if its total weight exceeds capacity.

## 3. QUBO Formulation and Penalty Analysis

The constrained problem must be converted into a Quadratic Unconstrained Binary Optimization (QUBO) problem before it can be used to construct the QAOA cost Hamiltonian.

The required Phase 2 formulation uses five item-selection bits and four binary slack bits, giving nine binary variables in total. The penalty parameter must be \(P=5\), as specified by the challenge.

The slack variables represent unused capacity and allow the capacity constraint to be encoded in the QUBO objective. The penalty term discourages assignments that violate the capacity equality in the encoded formulation.

For the original five-item problem, feasibility must ultimately be checked using the item-selection bits:

\[
\operatorname{feasible}(x)=
\begin{cases}
1,&\sum_i w_i x_i\leq 15,\\
0,&\text{otherwise}.
\end{cases}
\]

The implementation must calculate the original item value independently of the slack-bit assignment. Slack variables are auxiliary encoding variables; they do not represent additional items.

### 3.1 Baseline formulation versus required formulation

The earlier five-qubit baseline uses the penalty objective documented in the existing implementation:

\[
E(x)=-V(x)+P\bigl(w(x)-W\bigr)^2
+L\bigl(w(x)-W\bigr),
\]

where \(w(x)=\sum_i w_i x_i\), with \(P=1\) and \(L=1\) in that baseline.

This baseline must be distinguished from the required nine-qubit slack-variable formulation with \(P=5\). The two formulations have different encodings and cannot be treated as interchangeable.

A quadratic penalty does not automatically guarantee that the unconstrained QUBO ground state corresponds to the exact constrained optimum for every penalty choice. The QUBO ground state must therefore be compared with the exhaustive classical reference.

### 3.2 Penalty and optimization sensitivity

Penalty strength affects the balance between maximizing value and discouraging invalid assignments. An insufficient penalty can allow an infeasible assignment to have lower energy than a feasible assignment. An excessively strong penalty can also change the optimization landscape and make parameter selection more difficult.

The report should distinguish between the official scored configuration and any additional exploratory experiments. The official \(P=5\) configuration must remain unchanged for the required evaluation. Alternative penalty values, if investigated, should be reported separately and must not replace the official result.

## 4. Experimental Methodology

The experiment uses QAOA to prepare a quantum state whose measurement distribution can be analyzed for candidate item selections.

The baseline implementation uses p=1 QAOA and a deterministic grid search over \((\gamma,\beta)\) using an ideal statevector simulation. The selected parameters are then used for the corresponding noisy processor simulations in that baseline.

For the Phase 2 submission, the actual notebook must implement and document the required nine-qubit formulation, official settings, and Processor B evaluation procedure.

The experiment should follow these steps:

1. Construct the required QUBO and its cost Hamiltonian.
2. Prepare the QAOA circuit using the specified depth and parameters.
3. Evaluate the circuit using the prescribed simulation configuration.
4. Transpile the circuit for the relevant processor coupling map.
5. Sample the circuit using the prescribed shot count and noise model.
6. Decode the five item-selection bits from each measured candidate.
7. Calculate feasibility, item value, optimal-value hit rate, and circuit-resource metrics.
8. Compare the results with exhaustive classical enumeration and the random baseline.
9. Generate the required objective-landscape and processor-comparison figures.
10. Save the measured outputs in the official results format.

For the earlier baseline, noisy sampling used 4096 shots and transpilation used optimization level 1 with seed 42. These settings should be documented as Phase 2 settings only if they match the actual official configuration and the executed notebook.

## 5. Results and Benchmarking

All numerical results in this section must be populated from the completed experiment. The existing baseline outputs are not substitutes for the required Phase 2 results.

### 5.1 Processor and circuit resources

The baseline implementation generates processor metrics in `results/tables/processor_metrics.csv`. These measurements should be checked against the actual nine-qubit experiment before being used in the final Phase 2 analysis.

| Metric | Processor A | Processor B | Processor D |
|---|---|---|---|
| Qubits in configuration | 5 | 9 | Record actual count |
| Transpiled circuit depth | Not yet verified | Not yet verified | Not yet verified |
| Transpiled CX count | Not yet verified | Not yet verified | Not yet verified |
| Routing overhead | Not yet verified | Not yet verified | Not yet verified |
| Feasible-shot probability | Not yet verified | Not yet verified | Not yet verified |
| Optimal-value hit rate | Not yet verified | Not yet verified | Not yet verified |

Replace the placeholder entries with measurements from the official experiment. If a metric is not applicable or cannot be measured, explain why rather than inventing a value.

### 5.2 Solution quality and feasibility

For each processor and required experiment, report the following quantities:

- **Feasible-shot probability:** the fraction of measured candidates whose item-selection bits satisfy the capacity constraint.
- **Best feasible value:** the highest total item value observed among feasible candidates.
- **Optimal-value hit rate:** the fraction of measured candidates whose feasible item-selection value equals the classical optimum of 26.
- **Mean feasible value:** the mean
