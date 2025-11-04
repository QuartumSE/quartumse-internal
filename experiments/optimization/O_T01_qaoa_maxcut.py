"""O-T01: QAOA MAX-CUT with Shot-Frugal Cost Estimation.

This experiment demonstrates shot-frugal QAOA optimization using classical shadows
for cost function estimation on a 5-node ring graph with MAX-CUT objective.

Phase 1 Target: ≥20% reduction in optimizer steps vs. standard QAOA while
maintaining solution quality ≥0.90 approximation ratio.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit
from scipy.optimize import minimize

# Load environment (for IBM credentials)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from quartumse import ShadowEstimator
from quartumse.reporting.manifest import MitigationConfig
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.utils.args import (
    DEFAULT_DATA_DIR,
    add_backend_option,
    add_data_dir_option,
    add_seed_option,
    add_shadow_size_option,
)


class RingGraph:
    """5-node ring graph for MAX-CUT problem."""

    def __init__(self, num_nodes: int = 5):
        """
        Create ring graph topology.

        Args:
            num_nodes: Number of nodes (default: 5)
        """
        self.num_nodes = num_nodes
        self.edges = [(i, (i + 1) % num_nodes) for i in range(num_nodes)]

    def max_cut_hamiltonian(self) -> List[Observable]:
        """
        Construct MAX-CUT Hamiltonian for ring graph.

        H_C = (1/2) * sum_{(i,j) in E} (I - Z_i*Z_j)
            = constant - (1/2) * sum_{(i,j) in E} Z_i*Z_j

        Returns:
            List of observables (ZZ terms for each edge)
        """
        observables = []

        for i, j in self.edges:
            # Create ZZ term: Z_i * Z_j
            pauli_str = ["I"] * self.num_nodes
            pauli_str[i] = "Z"
            pauli_str[j] = "Z"

            # Coefficient: -0.5 for cost function (we minimize, so want negative)
            observables.append(Observable("".join(pauli_str), coefficient=-0.5))

        return observables

    def classical_optimal_cut(self) -> Tuple[float, str]:
        """
        Compute classical optimal MAX-CUT value and solution.

        For 5-node ring, optimal cut is 4 edges (one partition: {0,2}, {1,3,4}).

        Returns:
            (optimal_cost, optimal_bitstring)
        """
        # For odd ring, max cut = num_nodes - 1 = 4
        # One optimal solution: 10110 (nodes 0,2 vs 1,3,4)
        optimal_cut_size = 4
        optimal_cost = optimal_cut_size  # MAX-CUT objective
        optimal_bitstring = "10110"  # Example optimal partition

        return optimal_cost, optimal_bitstring


def create_qaoa_circuit(
    graph: RingGraph, params: np.ndarray, p: int = 1
) -> QuantumCircuit:
    """
    Create QAOA circuit for MAX-CUT on ring graph.

    Circuit structure:
    1. Initialize: |+⟩⊗n (Hadamard on all qubits)
    2. For layer k = 1 to p:
       - Cost layer: exp(-i * γ_k * H_C) (ZZ rotations)
       - Mixer layer: exp(-i * β_k * H_M) (X rotations)

    Args:
        graph: Ring graph instance
        params: QAOA parameters [γ_1, β_1, ..., γ_p, β_p] (length 2p)
        p: Ansatz depth (number of QAOA layers)

    Returns:
        QAOA circuit
    """
    num_qubits = graph.num_nodes
    qc = QuantumCircuit(num_qubits)

    # Initialize: |+⟩⊗n
    for i in range(num_qubits):
        qc.h(i)

    # QAOA layers
    for layer in range(p):
        gamma = params[2 * layer]
        beta = params[2 * layer + 1]

        # Cost layer: exp(-i * γ * H_C)
        for i, j in graph.edges:
            # ZZ interaction: exp(-i * γ * Z_i * Z_j)
            # Implemented as: CX(i,j) - RZ(2*γ) - CX(i,j)
            qc.cx(i, j)
            qc.rz(2 * gamma, j)
            qc.cx(i, j)

        # Mixer layer: exp(-i * β * H_M) where H_M = sum_i X_i
        for i in range(num_qubits):
            qc.rx(2 * beta, i)

    return qc


class QAOAOptimizer:
    """QAOA optimizer with shadow-based cost function estimation."""

    def __init__(
        self,
        graph: RingGraph,
        estimator: ShadowEstimator,
        observables: List[Observable],
        p: int = 1,
        max_iterations: int = 60,
    ):
        """
        Initialize QAOA optimizer.

        Args:
            graph: Ring graph instance
            estimator: Shadow estimator for cost function evaluation
            observables: MAX-CUT Hamiltonian observables
            p: QAOA ansatz depth
            max_iterations: Maximum optimizer iterations
        """
        self.graph = graph
        self.estimator = estimator
        self.observables = observables
        self.p = p
        self.max_iterations = max_iterations

        # Tracking
        self.iteration = 0
        self.convergence_history = []
        self.best_params = None
        self.best_cost = float("inf")

    def evaluate_cost(self, params: np.ndarray) -> float:
        """
        Evaluate QAOA cost function using shadow estimation.

        Args:
            params: QAOA parameters [γ_1, β_1, ..., γ_p, β_p]

        Returns:
            Cost function value (to minimize)
        """
        self.iteration += 1

        # Build QAOA circuit
        qc = create_qaoa_circuit(self.graph, params, self.p)

        # Estimate cost using shadows
        start_time = time.time()
        result = self.estimator.estimate(
            circuit=qc,
            observables=self.observables,
            save_manifest=False,  # Save only at convergence
        )
        eval_time = time.time() - start_time

        # Compute total cost: sum of all ZZ expectations
        cost = 0.0
        ci_widths = []
        for obs_str, obs_data in result.observables.items():
            cost += obs_data["expectation_value"]
            ci_widths.append(obs_data["ci_width"])

        # Add constant offset: MAX-CUT = (num_edges/2) - cost
        # (Since H_C = constant - (1/2) * sum ZZ, minimizing cost maximizes cut)
        num_edges = len(self.graph.edges)
        max_cut_value = (num_edges / 2) - cost

        # Track convergence
        mean_ci_width = float(np.mean(ci_widths))
        self.convergence_history.append(
            {
                "iteration": self.iteration,
                "params": params.tolist(),
                "cost": cost,
                "max_cut_value": max_cut_value,
                "mean_ci_width": mean_ci_width,
                "eval_time": eval_time,
            }
        )

        # Update best
        if cost < self.best_cost:
            self.best_cost = cost
            self.best_params = params.copy()

        # Print progress
        print(
            f"  Iter {self.iteration:3d}: cost={cost:.4f}, "
            f"cut={max_cut_value:.4f}, CI_width={mean_ci_width:.4f}, "
            f"time={eval_time:.2f}s"
        )

        return cost

    def optimize(
        self, initial_params: Optional[np.ndarray] = None, method: str = "COBYLA"
    ) -> Dict[str, Any]:
        """
        Run QAOA optimization.

        Args:
            initial_params: Initial parameter guess (random if None)
            method: Optimizer method (COBYLA, SLSQP, etc.)

        Returns:
            Optimization results dictionary
        """
        print(f"\n{'=' * 60}")
        print(f"QAOA Optimization (p={self.p}, method={method})")
        print(f"{'=' * 60}")

        # Initialize parameters
        if initial_params is None:
            # Random initialization in [0, π]
            initial_params = np.random.uniform(0, np.pi, 2 * self.p)

        print(f"Initial params: {initial_params}")

        # Optimize
        start_time = time.time()
        result = minimize(
            self.evaluate_cost,
            initial_params,
            method=method,
            options={"maxiter": self.max_iterations},
        )
        total_time = time.time() - start_time

        print(f"\nOptimization completed in {total_time:.2f}s")
        print(f"Converged: {result.success}")
        print(f"Final params: {result.x}")
        print(f"Final cost: {result.fun:.4f}")

        # Compute final MAX-CUT value and approximation ratio
        num_edges = len(self.graph.edges)
        final_max_cut = (num_edges / 2) - result.fun
        optimal_cut, _ = self.graph.classical_optimal_cut()
        approx_ratio = final_max_cut / optimal_cut

        print(f"\nFinal MAX-CUT value: {final_max_cut:.4f}")
        print(f"Optimal MAX-CUT: {optimal_cut}")
        print(f"Approximation ratio: {approx_ratio:.4f}")

        return {
            "success": result.success,
            "final_params": result.x.tolist(),
            "final_cost": result.fun,
            "final_max_cut": final_max_cut,
            "optimal_cut": optimal_cut,
            "approx_ratio": approx_ratio,
            "iterations": self.iteration,
            "total_time": total_time,
            "convergence_history": self.convergence_history,
        }


def run_experiment(
    backend: str = "aer_simulator",
    shadow_size: int = 300,
    shadow_version: str = "v0",
    p: int = 1,
    optimizer_method: str = "COBYLA",
    max_iterations: int = 60,
    seed: int = 42,
    mem_shots: int = 128,
    data_dir: Optional[Union[str, Path]] = None,
    trial_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run O-T01 QAOA MAX-CUT experiment.

    Args:
        backend: Backend descriptor (e.g., "ibm:ibm_fez", "aer_simulator")
        shadow_size: Number of shadows per cost evaluation
        shadow_version: Shadow version ("v0" or "v1")
        p: QAOA ansatz depth
        optimizer_method: Scipy optimizer method
        max_iterations: Maximum optimizer iterations
        seed: Random seed
        mem_shots: Calibration shots for MEM (if v1)
        data_dir: Data directory for manifests
        trial_id: Trial identifier (for multiple runs)

    Returns:
        Experiment results dictionary
    """
    print("=" * 80)
    print("O-T01: QAOA MAX-CUT with Shot-Frugal Cost Estimation")
    print("=" * 80)
    print(f"Backend: {backend}")
    print(f"Shadow size: {shadow_size}")
    print(f"Shadow version: {shadow_version}")
    print(f"QAOA depth (p): {p}")
    print(f"Optimizer: {optimizer_method}")
    print(f"Max iterations: {max_iterations}")
    print(f"Random seed: {seed}")
    print("=" * 80)

    # Set random seed
    np.random.seed(seed)

    # Create ring graph
    graph = RingGraph(num_nodes=5)
    print(f"\n5-node ring graph:")
    print(f"  Nodes: {graph.num_nodes}")
    print(f"  Edges: {graph.edges}")

    # MAX-CUT Hamiltonian
    observables = graph.max_cut_hamiltonian()
    print(f"\nMAX-CUT Hamiltonian ({len(observables)} terms):")
    for obs in observables:
        print(f"  {obs}")

    # Classical optimal
    optimal_cut, optimal_bitstring = graph.classical_optimal_cut()
    print(f"\nClassical optimal:")
    print(f"  MAX-CUT size: {optimal_cut}")
    print(f"  Example partition: {optimal_bitstring}")

    # Shadow configuration
    use_noise_aware = shadow_version.lower() == "v1"
    shadow_config = ShadowConfig(
        shadow_size=shadow_size,
        random_seed=seed,
        confidence_level=0.95,
        version=(
            ShadowVersion.V1_NOISE_AWARE if use_noise_aware else ShadowVersion.V0_BASELINE
        ),
        apply_inverse_channel=use_noise_aware,
    )

    mitigation_config = None
    if use_noise_aware:
        mitigation_config = MitigationConfig(
            techniques=["MEM"],
            parameters={"mem_shots": mem_shots},
        )

    # Data directory
    resolved_data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    resolved_data_dir.mkdir(parents=True, exist_ok=True)

    # Shadow estimator
    estimator = ShadowEstimator(
        backend=backend,
        shadow_config=shadow_config,
        mitigation_config=mitigation_config,
        data_dir=resolved_data_dir,
    )

    # QAOA optimizer
    optimizer = QAOAOptimizer(
        graph=graph,
        estimator=estimator,
        observables=observables,
        p=p,
        max_iterations=max_iterations,
    )

    # Run optimization
    optimization_result = optimizer.optimize(method=optimizer_method)

    # Save final manifest with best circuit
    print(f"\n{'=' * 60}")
    print("Saving final manifest...")
    print(f"{'=' * 60}")

    best_circuit = create_qaoa_circuit(graph, np.array(optimization_result["final_params"]), p)
    final_result = estimator.estimate(
        circuit=best_circuit,
        observables=observables,
        save_manifest=True,
    )

    print(f"Manifest saved: {final_result.manifest_path}")

    # Save convergence log
    trial_suffix = f"-trial-{trial_id:02d}" if trial_id is not None else ""
    convergence_log_path = (
        resolved_data_dir / "logs" / f"o-t01{trial_suffix}-convergence.json"
    )
    convergence_log_path.parent.mkdir(parents=True, exist_ok=True)

    convergence_data = {
        "experiment_id": "o-t01",
        "trial_id": trial_id,
        "backend": backend,
        "shadow_size": shadow_size,
        "shadow_version": shadow_version,
        "p": p,
        "optimizer": optimizer_method,
        "seed": seed,
        "convergence_history": optimization_result["convergence_history"],
        "final_results": {
            "approx_ratio": optimization_result["approx_ratio"],
            "iterations": optimization_result["iterations"],
            "total_time": optimization_result["total_time"],
            "final_params": optimization_result["final_params"],
        },
        "manifest_path": str(final_result.manifest_path),
    }

    with convergence_log_path.open("w", encoding="utf-8") as f:
        json.dump(convergence_data, f, indent=2)

    print(f"Convergence log saved: {convergence_log_path}")

    # Summary
    print(f"\n{'=' * 80}")
    print("EXPERIMENT SUMMARY")
    print(f"{'=' * 80}")
    print(f"Approximation ratio: {optimization_result['approx_ratio']:.4f} (target: ≥0.90)")
    print(f"Iterations to convergence: {optimization_result['iterations']}")
    print(f"Total shots: {shadow_size * optimization_result['iterations']}")
    print(f"Total time: {optimization_result['total_time']:.2f}s")

    # Success criteria
    approx_ratio_pass = optimization_result["approx_ratio"] >= 0.90
    print(f"\nPhase 1 Success Criteria:")
    print(f"  Approx Ratio ≥ 0.90: {'✓ PASS' if approx_ratio_pass else '✗ FAIL'}")
    print(f"  Manifest Generated: ✓ PASS")
    print(f"  Convergence Logged: ✓ PASS")

    print(f"\n{'=' * 80}")

    return optimization_result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run O-T01 QAOA MAX-CUT experiment with shot-frugal shadow estimation."
    )
    add_backend_option(parser)
    add_shadow_size_option(parser, default=300)
    add_seed_option(parser, default=42)
    add_data_dir_option(parser)

    parser.add_argument(
        "--shadow-version",
        type=str,
        default="v0",
        choices=["v0", "v1"],
        help="Shadow version (v0=baseline, v1=noise-aware with MEM)",
    )
    parser.add_argument(
        "--p",
        type=int,
        default=1,
        help="QAOA ansatz depth (number of layers)",
    )
    parser.add_argument(
        "--optimizer",
        type=str,
        default="COBYLA",
        choices=["COBYLA", "SLSQP", "Powell"],
        help="Scipy optimizer method",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=60,
        help="Maximum optimizer iterations",
    )
    parser.add_argument(
        "--mem-shots",
        type=int,
        default=128,
        help="Calibration shots for MEM (if using v1)",
    )
    parser.add_argument(
        "--trial-id",
        type=int,
        default=None,
        help="Trial identifier (for running multiple independent trials)",
    )

    args = parser.parse_args()

    run_experiment(
        backend=args.backend,
        shadow_size=args.shadow_size,
        shadow_version=args.shadow_version,
        p=args.p,
        optimizer_method=args.optimizer,
        max_iterations=args.max_iterations,
        seed=args.seed,
        mem_shots=args.mem_shots,
        data_dir=args.data_dir,
        trial_id=args.trial_id,
    )
