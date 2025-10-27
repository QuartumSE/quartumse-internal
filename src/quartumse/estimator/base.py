"""Base estimator interface."""

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from qiskit import QuantumCircuit

from quartumse.shadows.core import Observable


@dataclass(slots=True)
class EstimationResult:
    """Result container for observable estimation."""

    observables: Dict[str, Any]
    shots_used: int
    execution_time: float
    backend_name: str
    experiment_id: Optional[str] = None
    manifest_path: Optional[str] = None
    shot_data_path: Optional[str] = None
    mitigation_confusion_matrix_path: Optional[str] = None

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

    def __init__(self, backend: Any, config: Optional[Any] = None) -> None:
        self.backend = backend
        self.config = config

    @abstractmethod
    def estimate(
        self,
        circuit: QuantumCircuit,
        observables: List[Observable],
        target_precision: Optional[float] = None,
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
    def estimate_shots_needed(
        self, observables: List[Observable], target_precision: float
    ) -> int:
        """
        Estimate number of shots needed for target precision.

        Used for cost estimation and shot allocation.
        """
        raise NotImplementedError
