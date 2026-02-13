"""Abstract base class for measurement protocols (Measurements Bible §5).

This module defines the Protocol abstract base class that all measurement
protocols must implement. The interface supports both static and adaptive
protocols through a five-method contract:

1. initialize() - Set up protocol state
2. next_plan() - Generate measurement plan (can be called multiple times for adaptive)
3. acquire() - Execute measurements
4. update() - Update state with new data
5. finalize() - Produce final estimates

Static protocols implement next_plan to return a single plan consuming the
full budget, while adaptive protocols may return multiple plans across rounds.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from .state import (
    Estimates,
    MeasurementPlan,
    ProtocolState,
    RawDatasetChunk,
)

if TYPE_CHECKING:
    from quartumse.observables.core import ObservableSet


class ProtocolConfig:
    """Configuration for a measurement protocol.

    Attributes:
        confidence_level: Target confidence level for CIs (default 0.95).
        random_seed: Random seed for reproducibility.
        bootstrap_replicates: Number of bootstrap replicates for CI (default 1000).
        ci_method: CI construction method override (None = auto-select).
        clamp_bounds: Whether to clamp CI bounds to valid range.
        clamp_range: Range for clamping (default [-1, 1] for Pauli observables).
        max_rounds: Maximum number of adaptive rounds (default 1 for static).
        extra: Additional protocol-specific configuration.
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        random_seed: int | None = None,
        bootstrap_replicates: int = 1000,
        ci_method: str | None = None,
        clamp_bounds: bool = True,
        clamp_range: tuple[float, float] = (-1.0, 1.0),
        max_rounds: int = 1,
        **extra: Any,
    ) -> None:
        self.confidence_level = confidence_level
        self.random_seed = random_seed
        self.bootstrap_replicates = bootstrap_replicates
        self.ci_method = ci_method
        self.clamp_bounds = clamp_bounds
        self.clamp_range = clamp_range
        self.max_rounds = max_rounds
        self.extra = extra

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "confidence_level": self.confidence_level,
            "random_seed": self.random_seed,
            "bootstrap_replicates": self.bootstrap_replicates,
            "ci_method": self.ci_method,
            "clamp_bounds": self.clamp_bounds,
            "clamp_range": self.clamp_range,
            "max_rounds": self.max_rounds,
            **self.extra,
        }


class Protocol(ABC):
    """Abstract base class for measurement protocols (§5.1).

    All protocols must implement this interface. The five-method contract
    supports both static and adaptive protocols:

    Static protocols:
    - next_plan() returns a single plan consuming the full budget
    - update() only accumulates data
    - finalize() performs one-shot estimation

    Adaptive protocols:
    - next_plan() may be called multiple times
    - update() may adjust internal state based on accumulated data
    - Can implement early stopping via state.converged

    Subclasses must implement:
    - protocol_id (class attribute): Unique identifier
    - protocol_version (class attribute): Semantic version
    - initialize(): Set up initial state
    - next_plan(): Generate measurement plan
    - acquire(): Execute measurements
    - update(): Update state with new data
    - finalize(): Produce final estimates
    """

    # Subclasses must override these
    protocol_id: str = "abstract_protocol"
    protocol_version: str = "0.0.0"

    def __init__(self, config: ProtocolConfig | None = None) -> None:
        """Initialize protocol with configuration.

        Args:
            config: Protocol configuration. Uses defaults if None.
        """
        self.config = config or ProtocolConfig()

    @abstractmethod
    def initialize(
        self,
        observable_set: ObservableSet,
        total_budget: int,
        seed: int,
    ) -> ProtocolState:
        """Initialize protocol state for a new estimation task (§5.1).

        This method is called once at the start of estimation to set up
        the protocol's internal state.

        Args:
            observable_set: The set of observables to estimate.
            total_budget: Total shot budget for the estimation.
            seed: Random seed for reproducibility.

        Returns:
            Initialized ProtocolState.
        """
        ...

    @abstractmethod
    def next_plan(
        self,
        state: ProtocolState,
        remaining_budget: int,
    ) -> MeasurementPlan:
        """Generate the next measurement plan (§5.1).

        For static protocols, this returns a single plan consuming the
        full budget. For adaptive protocols, this may return partial plans
        to be executed iteratively.

        Args:
            state: Current protocol state.
            remaining_budget: Remaining shot budget.

        Returns:
            MeasurementPlan specifying settings and shot allocation.
        """
        ...

    @abstractmethod
    def acquire(
        self,
        circuit: QuantumCircuit,
        plan: MeasurementPlan,
        backend: AerSimulator | Any,
        seed: int,
    ) -> RawDatasetChunk:
        """Execute measurements according to the plan (§5.1).

        This method generates measurement circuits, executes them on the
        backend, and returns raw measurement outcomes.

        Args:
            circuit: The state preparation circuit.
            plan: Measurement plan to execute.
            backend: Quantum backend for execution.
            seed: Random seed for measurement randomness.

        Returns:
            RawDatasetChunk containing measurement outcomes.
        """
        ...

    @abstractmethod
    def update(
        self,
        state: ProtocolState,
        data_chunk: RawDatasetChunk,
    ) -> ProtocolState:
        """Update protocol state with new measurement data (§5.1).

        For static protocols, this simply accumulates data. For adaptive
        protocols, this may update variance estimates, convergence checks,
        or other internal state used for planning.

        Args:
            state: Current protocol state.
            data_chunk: New measurement data.

        Returns:
            Updated ProtocolState.
        """
        ...

    @abstractmethod
    def finalize(
        self,
        state: ProtocolState,
        observable_set: ObservableSet,
    ) -> Estimates:
        """Produce final estimates from accumulated data (§5.1).

        This method processes all accumulated measurement data to produce
        final expectation value estimates with uncertainty quantification.

        Args:
            state: Final protocol state with all accumulated data.
            observable_set: The observables to estimate.

        Returns:
            Estimates containing per-observable results.
        """
        ...

    def run(
        self,
        circuit: QuantumCircuit,
        observable_set: ObservableSet,
        total_budget: int,
        backend: AerSimulator | Any,
        seed: int | None = None,
    ) -> Estimates:
        """Execute the full protocol pipeline.

        This is a convenience method that runs the full initialize ->
        (next_plan -> acquire -> update)* -> finalize loop.

        Args:
            circuit: State preparation circuit.
            observable_set: Observables to estimate.
            total_budget: Total shot budget.
            backend: Quantum backend.
            seed: Random seed (uses config.random_seed if None).

        Returns:
            Final Estimates.
        """
        seed = seed if seed is not None else (self.config.random_seed or 42)

        # Initialize
        state = self.initialize(observable_set, total_budget, seed)
        remaining = total_budget
        round_seed = seed

        start_time = time.time()

        # Main loop (single iteration for static protocols)
        while remaining > 0 and not state.converged:
            if state.n_rounds >= self.config.max_rounds:
                break

            # Plan
            plan = self.next_plan(state, remaining)
            if plan.total_shots == 0:
                break

            # Acquire
            round_start = time.time()
            chunk = self.acquire(circuit, plan, backend, round_seed)
            quantum_time = time.time() - round_start

            # Update
            classical_start = time.time()
            state = self.update(state, chunk)
            classical_time = time.time() - classical_start

            # Record round metadata (append if update() didn't already)
            if len(state.round_metadata) < state.n_rounds:
                state.round_metadata.append({})
            state.round_metadata[-1].update(
                {
                    "quantum_time_s": quantum_time,
                    "classical_time_s": classical_time,
                    "shots_this_round": chunk.n_shots,
                    "settings_this_round": plan.n_settings,
                }
            )

            remaining -= chunk.n_shots
            round_seed += 1

        # Finalize
        estimates = self.finalize(state, observable_set)
        estimates.raw_chunks = state.accumulated_data

        # Add timing and protocol info
        total_time = time.time() - start_time
        estimates.time_quantum_s = sum(m.get("quantum_time_s", 0) for m in state.round_metadata)
        estimates.time_classical_s = total_time - (estimates.time_quantum_s or 0)
        estimates.protocol_id = self.protocol_id
        estimates.protocol_version = self.protocol_version

        return estimates

    def get_info(self) -> dict[str, Any]:
        """Get protocol information for manifest/logging."""
        return {
            "protocol_id": self.protocol_id,
            "protocol_version": self.protocol_version,
            "config": self.config.to_dict(),
        }


class StaticProtocol(Protocol):
    """Base class for static (non-adaptive) protocols.

    Static protocols execute a single plan consuming the full budget.
    This class provides default implementations that simplify the
    interface for non-adaptive use cases.

    Subclasses should implement:
    - initialize(): Set up initial state
    - plan(): Generate the measurement plan (called by next_plan)
    - finalize(): Produce final estimates

    The next_plan() and acquire() methods have default implementations
    that delegate to plan() and simulate measurements respectively.
    """

    def next_plan(
        self,
        state: ProtocolState,
        remaining_budget: int,
    ) -> MeasurementPlan:
        """Generate next measurement plan by delegating to plan().

        Static protocols return a single plan consuming the full budget.
        This method bridges the Protocol ABC interface to the simpler
        plan() method that static protocols implement.

        Args:
            state: Current protocol state.
            remaining_budget: Remaining shot budget.

        Returns:
            MeasurementPlan from plan() method.
        """
        return self.plan(state)

    def plan(self, state: ProtocolState) -> MeasurementPlan:
        """Generate the measurement plan for this protocol.

        Subclasses must override this method.

        Args:
            state: Current protocol state.

        Returns:
            MeasurementPlan specifying settings and shot allocation.
        """
        raise NotImplementedError("Subclasses must implement plan()")

    def acquire(
        self,
        circuit: QuantumCircuit,
        plan: MeasurementPlan,
        backend: AerSimulator | Any,
        seed: int,
    ) -> RawDatasetChunk:
        """Execute measurements according to the plan.

        Default implementation executes measurement circuits using the
        provided backend or sampler.

        Args:
            circuit: The state preparation circuit.
            plan: Measurement plan to execute.
            backend: Quantum backend for execution.
            seed: Random seed for measurement randomness.

        Returns:
            RawDatasetChunk containing measurement outcomes.
        """
        from qiskit_aer import AerSimulator

        bitstrings: dict[str, list[str]] = {}
        backend = backend or AerSimulator()

        for setting, n_shots in zip(plan.settings, plan.shots_per_setting, strict=False):
            measurement_circuit = self._build_measurement_circuit(
                circuit=circuit,
                measurement_basis=setting.measurement_basis,
                target_qubits=setting.target_qubits,
            )

            setting_bitstrings = self._execute_measurement_circuit(
                circuit=measurement_circuit,
                backend=backend,
                n_shots=n_shots,
                seed=seed,
            )

            bitstrings[setting.setting_id] = setting_bitstrings

        return RawDatasetChunk(
            bitstrings=bitstrings,
            settings_executed=list(bitstrings.keys()),
            n_qubits=circuit.num_qubits,
        )

    def _build_measurement_circuit(
        self,
        circuit: QuantumCircuit,
        measurement_basis: str,
        target_qubits: list[int] | None,
    ) -> QuantumCircuit:
        """Construct a measurement circuit matching the requested basis."""
        base_circuit = circuit.remove_final_measurements(inplace=False)
        basis = self._expand_basis(
            measurement_basis,
            base_circuit.num_qubits,
            target_qubits,
        )
        measurement_circuit = base_circuit.copy()

        for qubit, basis_char in enumerate(basis):
            if basis_char == "X":
                measurement_circuit.h(qubit)
            elif basis_char == "Y":
                measurement_circuit.sdg(qubit)
                measurement_circuit.h(qubit)

        measurement_circuit.measure_all()

        # Verify measurements were added
        if measurement_circuit.num_clbits == 0:
            raise RuntimeError(
                f"measure_all() did not add classical bits. "
                f"Circuit: {circuit.name}, basis={basis}, "
                f"num_qubits={measurement_circuit.num_qubits}"
            )

        return measurement_circuit

    def _expand_basis(
        self,
        measurement_basis: str,
        n_qubits: int,
        target_qubits: list[int] | None,
    ) -> str:
        """Expand a basis string to cover all qubits."""
        if not measurement_basis:
            return "Z" * n_qubits

        if len(measurement_basis) == n_qubits:
            return measurement_basis.replace("I", "Z")

        basis = ["Z"] * n_qubits
        if target_qubits:
            if len(measurement_basis) == len(target_qubits):
                for basis_char, qubit in zip(measurement_basis, target_qubits, strict=False):
                    basis[qubit] = basis_char
            else:
                for qubit in target_qubits:
                    if qubit < len(measurement_basis):
                        basis[qubit] = measurement_basis[qubit]
        return "".join(basis).replace("I", "Z")

    def _execute_measurement_circuit(
        self,
        circuit: QuantumCircuit,
        backend: Any,
        n_shots: int,
        seed: int,
    ) -> list[str]:
        """Execute a measurement circuit and return normalized bitstrings."""
        if hasattr(backend, "sample"):
            result = backend.sample(circuit, n_shots=n_shots, seed=seed)
            bitstrings = result.bitstrings
        else:
            from qiskit import transpile

            # Verify circuit has measurements before running
            if circuit.num_clbits == 0:
                raise ValueError(
                    f"Circuit has no classical bits for measurement. "
                    f"name={circuit.name}, num_qubits={circuit.num_qubits}, "
                    f"num_clbits={circuit.num_clbits}"
                )

            compiled = transpile(circuit, backend)
            job = backend.run(compiled, shots=n_shots, seed_simulator=seed)
            result = job.result()

            try:
                counts = result.get_counts()
            except Exception as e:
                raise RuntimeError(
                    f"No counts from circuit execution. "
                    f"name={circuit.name}, num_qubits={circuit.num_qubits}, "
                    f"num_clbits={circuit.num_clbits}, shots={n_shots}. "
                    f"Original error: {e}"
                ) from e

            bitstrings = []
            for bitstring in sorted(counts.keys()):
                count = counts[bitstring]
                cleaned = bitstring.replace(" ", "")
                bitstrings.extend([cleaned] * count)

        return [bs[::-1] for bs in bitstrings]

    def update(
        self,
        state: ProtocolState,
        data_chunk: RawDatasetChunk,
    ) -> ProtocolState:
        """Default update: just accumulate data."""
        state.add_chunk(data_chunk)
        return state


class AdaptiveProtocol(Protocol):
    """Base class for adaptive protocols.

    Adaptive protocols may execute multiple rounds, adjusting their
    measurement strategy based on accumulated data. This class provides
    additional infrastructure for adaptive decision-making.
    """

    def __init__(self, config: ProtocolConfig | None = None) -> None:
        super().__init__(config)
        # Default to more rounds for adaptive protocols
        if config is None:
            self.config.max_rounds = 10

    @abstractmethod
    def check_convergence(
        self,
        state: ProtocolState,
        observable_set: ObservableSet,
        target_precision: float | None = None,
    ) -> bool:
        """Check if the protocol has converged to sufficient precision.

        Args:
            state: Current protocol state.
            observable_set: Observables being estimated.
            target_precision: Optional target precision (epsilon).

        Returns:
            True if converged, False otherwise.
        """
        ...
