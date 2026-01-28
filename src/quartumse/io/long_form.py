"""Long-form results table builder (Measurements Bible §10.1).

This module provides utilities for constructing and managing the long-form
tidy data output table. Each row represents one observable estimate from
one protocol run.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from .schemas import JobStatus, LongFormRow


class LongFormResultBuilder:
    """Builder for constructing long-form result rows.

    This class provides a fluent interface for building LongFormRow objects
    with proper defaults and validation.

    Example:
        builder = LongFormResultBuilder()
        row = (
            builder
            .with_run_id("run_001")
            .with_circuit("circuit_001", n_qubits=4, depth=10)
            .with_observable("obs_001", "XXII", locality=2)
            .with_protocol("direct_naive", "1.0.0")
            .with_budget(N_total=1000, n_settings=1)
            .with_estimate(0.75, se=0.02)
            .with_truth(0.74, mode="exact_statevector")
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize builder with empty state."""
        self._data: dict[str, Any] = {
            "methodology_version": "1.0.0",
            "noise_profile_id": "ideal",
            "replicate_id": 0,
            "confidence_level": 0.95,
            "metadata": {},
        }

    def reset(self) -> LongFormResultBuilder:
        """Reset builder to initial state."""
        self._data = {
            "methodology_version": "1.0.0",
            "noise_profile_id": "ideal",
            "replicate_id": 0,
            "confidence_level": 0.95,
            "metadata": {},
        }
        return self

    def with_run_id(self, run_id: str | None = None) -> LongFormResultBuilder:
        """Set run identifier.

        Args:
            run_id: Unique run ID. Auto-generated if not provided.
        """
        self._data["run_id"] = run_id or f"run_{uuid4().hex[:12]}"
        return self

    def with_methodology_version(self, version: str) -> LongFormResultBuilder:
        """Set methodology version."""
        self._data["methodology_version"] = version
        return self

    def with_circuit(
        self,
        circuit_id: str,
        n_qubits: int,
        depth: int | None = None,
        twoq_gate_count: int | None = None,
    ) -> LongFormResultBuilder:
        """Set circuit information.

        Args:
            circuit_id: Circuit identifier.
            n_qubits: Number of qubits.
            depth: Circuit depth (optional).
            twoq_gate_count: Number of 2-qubit gates (optional).
        """
        self._data["circuit_id"] = circuit_id
        self._data["n_qubits"] = n_qubits
        self._data["circuit_depth"] = depth
        self._data["twoq_gate_count"] = twoq_gate_count
        return self

    def with_observable(
        self,
        observable_id: str,
        observable_type: str,
        locality: int,
        coefficient: float = 1.0,
        observable_set_id: str | None = None,
        group_id: str | None = None,
        M_total: int = 1,
    ) -> LongFormResultBuilder:
        """Set observable information.

        Args:
            observable_id: Observable identifier.
            observable_type: Type: pauli_string, pauli_sum, matrix.
            locality: Pauli weight / locality.
            coefficient: Observable coefficient.
            observable_set_id: Observable set ID.
            group_id: Commuting group ID (if grouped).
            M_total: Total number of observables in the set.
        """
        self._data["observable_id"] = observable_id
        self._data["observable_type"] = observable_type
        self._data["locality"] = locality
        self._data["coefficient"] = coefficient
        self._data["observable_set_id"] = observable_set_id or f"obsset_{uuid4().hex[:8]}"
        self._data["group_id"] = group_id
        self._data["M_total"] = M_total
        return self

    def with_protocol(
        self,
        protocol_id: str,
        protocol_version: str,
    ) -> LongFormResultBuilder:
        """Set protocol information.

        Args:
            protocol_id: Protocol identifier.
            protocol_version: Protocol version.
        """
        self._data["protocol_id"] = protocol_id
        self._data["protocol_version"] = protocol_version
        return self

    def with_backend(
        self,
        backend_id: str,
        noise_profile_id: str = "ideal",
    ) -> LongFormResultBuilder:
        """Set backend information.

        Args:
            backend_id: Backend identifier.
            noise_profile_id: Noise profile ID.
        """
        self._data["backend_id"] = backend_id
        self._data["noise_profile_id"] = noise_profile_id
        return self

    def with_replicate(self, replicate_id: int) -> LongFormResultBuilder:
        """Set replicate number.

        Args:
            replicate_id: Replicate number (0-indexed).
        """
        self._data["replicate_id"] = replicate_id
        return self

    def with_seeds(
        self,
        seed_policy: str,
        seed_protocol: int,
        seed_acquire: int,
        seed_bootstrap: int | None = None,
    ) -> LongFormResultBuilder:
        """Set random seeds for reproducibility.

        Args:
            seed_policy: Policy used to derive run seeds.
            seed_protocol: Seed for protocol planning.
            seed_acquire: Seed for measurement sampling.
            seed_bootstrap: Seed for bootstrap CI (optional).
        """
        self._data["seed_policy"] = seed_policy
        self._data["seed_protocol"] = seed_protocol
        self._data["seed_acquire"] = seed_acquire
        self._data["seed_bootstrap"] = seed_bootstrap
        return self

    def with_budget(
        self,
        N_total: int,
        n_settings: int,
    ) -> LongFormResultBuilder:
        """Set shot budget information.

        Args:
            N_total: Total shots used.
            n_settings: Number of distinct measurement settings.
        """
        self._data["N_total"] = N_total
        self._data["n_settings"] = n_settings
        return self

    def with_timing(
        self,
        time_quantum_s: float | None = None,
        time_classical_s: float | None = None,
        memory_bytes: int | None = None,
    ) -> LongFormResultBuilder:
        """Set timing and resource information.

        Args:
            time_quantum_s: Quantum execution time in seconds.
            time_classical_s: Classical processing time in seconds.
            memory_bytes: Peak memory usage.
        """
        self._data["time_quantum_s"] = time_quantum_s
        self._data["time_classical_s"] = time_classical_s
        self._data["memory_bytes"] = memory_bytes
        return self

    def with_cost(
        self,
        cost_model_id: str,
        cost_usd_estimate: float,
    ) -> LongFormResultBuilder:
        """Set cost information.

        Args:
            cost_model_id: Cost model identifier.
            cost_usd_estimate: Estimated cost in USD.
        """
        self._data["cost_model_id"] = cost_model_id
        self._data["cost_usd_estimate"] = cost_usd_estimate
        return self

    def with_hardware_status(
        self,
        job_status: JobStatus | str,
        queue_time_s: float | None = None,
        job_submitted_at: datetime | None = None,
        job_started_at: datetime | None = None,
        job_completed_at: datetime | None = None,
    ) -> LongFormResultBuilder:
        """Set hardware job status information.

        Args:
            job_status: Job execution status.
            queue_time_s: Queue time in seconds.
            job_submitted_at: Job submission timestamp.
            job_started_at: Job start timestamp.
            job_completed_at: Job completion timestamp.
        """
        if isinstance(job_status, str):
            job_status = JobStatus(job_status)
        self._data["job_status"] = job_status
        self._data["queue_time_s"] = queue_time_s
        self._data["job_submitted_at"] = job_submitted_at
        self._data["job_started_at"] = job_started_at
        self._data["job_completed_at"] = job_completed_at
        return self

    def with_estimate(
        self,
        estimate: float,
        se: float,
        ci_low: float | None = None,
        ci_high: float | None = None,
        ci_low_raw: float | None = None,
        ci_high_raw: float | None = None,
        ci_method_id: str | None = None,
        confidence_level: float = 0.95,
    ) -> LongFormResultBuilder:
        """Set estimation results.

        Args:
            estimate: Point estimate of expectation value.
            se: Standard error of the estimate.
            ci_low: CI lower bound (after clamping).
            ci_high: CI upper bound (after clamping).
            ci_low_raw: CI lower bound (before clamping).
            ci_high_raw: CI upper bound (before clamping).
            ci_method_id: CI construction method.
            confidence_level: Confidence level for CI.
        """
        self._data["estimate"] = estimate
        self._data["se"] = se
        self._data["ci_low"] = ci_low
        self._data["ci_high"] = ci_high
        self._data["ci_low_raw"] = ci_low_raw
        self._data["ci_high_raw"] = ci_high_raw
        self._data["ci_method_id"] = ci_method_id
        self._data["confidence_level"] = confidence_level
        return self

    def with_truth(
        self,
        truth_value: float,
        mode: str = "exact_statevector",
        truth_se: float | None = None,
    ) -> LongFormResultBuilder:
        """Set ground truth information.

        Args:
            truth_value: Ground truth expectation value.
            mode: Truth mode (exact_statevector, exact_density_matrix, reference).
            truth_se: SE of truth (if reference truth).
        """
        self._data["truth_value"] = truth_value
        self._data["truth_mode"] = mode
        self._data["truth_se"] = truth_se
        return self

    def with_metadata(self, **kwargs: Any) -> LongFormResultBuilder:
        """Add additional metadata.

        Args:
            **kwargs: Key-value pairs to add to metadata.
        """
        self._data["metadata"].update(kwargs)
        return self

    def build(self) -> LongFormRow:
        """Build the LongFormRow object.

        Returns:
            Validated LongFormRow.

        Raises:
            ValueError: If required fields are missing.
        """
        # Validate required fields
        required = [
            "run_id",
            "circuit_id",
            "observable_set_id",
            "observable_id",
            "protocol_id",
            "protocol_version",
            "backend_id",
            "seed_policy",
            "seed_protocol",
            "seed_acquire",
            "n_qubits",
            "observable_type",
            "locality",
            "N_total",
            "n_settings",
            "estimate",
            "se",
            "M_total",
        ]
        missing = [f for f in required if f not in self._data or self._data[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        row = LongFormRow(**self._data)

        # Compute derived metrics
        row.compute_derived_metrics()

        return row


class LongFormResultSet:
    """Collection of long-form result rows.

    Provides utilities for managing and querying result sets.
    """

    def __init__(self, rows: list[LongFormRow] | None = None) -> None:
        """Initialize with optional initial rows."""
        self._rows: list[LongFormRow] = rows or []

    def add(self, row: LongFormRow) -> None:
        """Add a row to the result set."""
        self._rows.append(row)

    def add_many(self, rows: list[LongFormRow]) -> None:
        """Add multiple rows to the result set."""
        self._rows.extend(rows)

    @property
    def rows(self) -> list[LongFormRow]:
        """Get all rows."""
        return self._rows

    def __len__(self) -> int:
        """Number of rows."""
        return len(self._rows)

    def __iter__(self):
        """Iterate over rows."""
        return iter(self._rows)

    def filter_by_protocol(self, protocol_id: str) -> LongFormResultSet:
        """Filter rows by protocol ID."""
        return LongFormResultSet([r for r in self._rows if r.protocol_id == protocol_id])

    def filter_by_circuit(self, circuit_id: str) -> LongFormResultSet:
        """Filter rows by circuit ID."""
        return LongFormResultSet([r for r in self._rows if r.circuit_id == circuit_id])

    def filter_by_budget(self, N_total: int) -> LongFormResultSet:
        """Filter rows by shot budget."""
        return LongFormResultSet([r for r in self._rows if r.N_total == N_total])

    def filter_by_observable(self, observable_id: str) -> LongFormResultSet:
        """Filter rows by observable ID."""
        return LongFormResultSet(
            [r for r in self._rows if r.observable_id == observable_id]
        )

    def get_unique_protocols(self) -> list[str]:
        """Get unique protocol IDs."""
        return list({r.protocol_id for r in self._rows})

    def get_unique_circuits(self) -> list[str]:
        """Get unique circuit IDs."""
        return list({r.circuit_id for r in self._rows})

    def get_unique_budgets(self) -> list[int]:
        """Get unique shot budgets."""
        return sorted({r.N_total for r in self._rows})

    def to_dicts(self) -> list[dict[str, Any]]:
        """Convert all rows to dictionaries."""
        return [r.model_dump() for r in self._rows]
