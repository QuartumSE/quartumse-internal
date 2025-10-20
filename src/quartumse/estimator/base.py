"""Base estimator interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from qiskit import QuantumCircuit

from quartumse.shadows.core import Observable


class EstimationResult:
    """Result container for observable estimation."""

    def __init__(
        self,
        observables: Dict[str, Any],
        shots_used: int,
        execution_time: float,
        backend_name: str,
        manifest_path: Optional[str] = None,
    ):
        self.observables = observables
        self.shots_used = shots_used
        self.execution_time = execution_time
        self.backend_name = backend_name
        self.manifest_path = manifest_path

    def __repr__(self) -> str:
        return (
            f"EstimationResult(observables={len(self.observables)}, "
            f"shots={self.shots_used}, "
            f"backend={self.backend_name})"
        )


class Estimator(ABC):
    """
    Abstract base class for quantum observable estimators.

    Provides unified interface for different estimation strategies:
    - Classical shadows (various versions)
    - Direct measurement
    - Grouped Pauli measurement
    """

    def __init__(self, backend: Any, config: Optional[Any] = None):
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
        pass

    @abstractmethod
    def estimate_shots_needed(
        self, observables: List[Observable], target_precision: float
    ) -> int:
        """
        Estimate number of shots needed for target precision.

        Used for cost estimation and shot allocation.
        """
        pass
