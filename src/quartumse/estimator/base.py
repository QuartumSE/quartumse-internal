"""Base estimator interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from qiskit import QuantumCircuit

from quartumse.shadows.core import Observable


@dataclass(slots=True)
class EstimationResult:
    """Result container for observable estimation."""

    observables: dict[str, Any]
    shots_used: int
    execution_time: float
    backend_name: str
    experiment_id: str | None = None
    manifest_path: str | None = None
    shot_data_path: str | None = None
    mitigation_confusion_matrix_path: str | None = None

    def __repr__(self) -> str:
        return (
            f"EstimationResult(observables={len(self.observables)}, "
            f"shots={self.shots_used}, "
            f"backend={self.backend_name}, "
            f"experiment_id={self.experiment_id})"
        )


class Estimator(ABC):
    """
    Abstract base class for quantum observable estimators.

    Provides unified interface for different estimation strategies:
    - Classical shadows (various versions)
    - Direct measurement
    - Grouped Pauli measurement
    """

    def __init__(self, backend: Any, config: Any | None = None) -> None:
        self.backend = backend
        self.config = config

    @abstractmethod
    def estimate(
        self,
        circuit: QuantumCircuit,
        observables: list[Observable],
        target_precision: float | None = None,
    ) -> EstimationResult:
        """
        Estimate expectation values of observables.

        Args:
            circuit: State preparation circuit
            observables: List of observables to estimate
            target_precision: Desired precision (optional)

        Returns:
            Estimation results with confidence intervals
        """
        raise NotImplementedError

    @abstractmethod
    def estimate_shots_needed(self, observables: list[Observable], target_precision: float) -> int:
        """
        Estimate number of shots needed for target precision.

        Used for cost estimation and shot allocation.
        """
        raise NotImplementedError
