"""Core observable representations (Measurements Bible §3.2).

This module defines the Observable and ObservableSet classes that represent
quantum observables with full metadata as required by §3.2.

Observable representations supported:
- Pauli string: e.g., "XYZII"
- Pauli sum: weighted sum of Pauli strings (Hamiltonian)
- Coefficient: multiplicative factor

Required metadata per §3.2:
- observable_id: unique identifier
- observable_type: pauli_string, pauli_sum, matrix
- locality: Pauli weight (number of non-identity factors)
- coefficient: if part of a sum
- group_id: for grouped baselines
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray


class ObservableType(Enum):
    """Type of observable representation."""

    PAULI_STRING = "pauli_string"
    PAULI_SUM = "pauli_sum"
    MATRIX = "matrix"


# Pauli matrices for reference
PAULI_I = np.array([[1, 0], [0, 1]], dtype=complex)
PAULI_X = np.array([[0, 1], [1, 0]], dtype=complex)
PAULI_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=complex)

PAULI_MATRICES = {"I": PAULI_I, "X": PAULI_X, "Y": PAULI_Y, "Z": PAULI_Z}


@dataclass
class Observable:
    """A quantum observable with full metadata (§3.2).

    An observable represents a Hermitian operator whose expectation value
    we want to estimate. The primary representation is a Pauli string
    (e.g., "XYZII") with an optional coefficient.

    Attributes:
        pauli_string: Pauli string representation (e.g., "XYZII").
        coefficient: Multiplicative coefficient (default 1.0).
        observable_id: Unique identifier. Auto-generated if not provided.
        group_id: Group identifier for commuting families (None if ungrouped).
        metadata: Additional observable-specific metadata.
    """

    pauli_string: str
    coefficient: float = 1.0
    observable_id: str | None = None
    group_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and set defaults."""
        # Validate Pauli string
        valid_chars = set("IXYZ")
        if not all(c in valid_chars for c in self.pauli_string):
            invalid = set(self.pauli_string) - valid_chars
            raise ValueError(
                f"Invalid characters in Pauli string: {invalid}. " f"Must be one of I, X, Y, Z."
            )

        # Auto-generate observable_id if not provided
        if self.observable_id is None:
            # Create a short hash-based ID
            hash_input = f"{self.pauli_string}:{self.coefficient}"
            short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
            self.observable_id = f"obs_{short_hash}"

    @property
    def n_qubits(self) -> int:
        """Number of qubits this observable acts on."""
        return len(self.pauli_string)

    @property
    def observable_type(self) -> ObservableType:
        """Type of observable representation."""
        return ObservableType.PAULI_STRING

    @property
    def locality(self) -> int:
        """Pauli weight (number of non-identity factors)."""
        return sum(1 for c in self.pauli_string if c != "I")

    @property
    def weight(self) -> int:
        """Alias for locality (Pauli weight)."""
        return self.locality

    @property
    def support(self) -> list[int]:
        """Qubit indices where this observable acts non-trivially."""
        return [i for i, c in enumerate(self.pauli_string) if c != "I"]

    def to_matrix(self) -> NDArray[np.complexfloating]:
        """Convert to matrix representation."""
        result = np.array([[1.0]], dtype=complex)
        for pauli_char in self.pauli_string:
            result = np.kron(result, PAULI_MATRICES[pauli_char])
        return self.coefficient * result

    def commutes_with(self, other: Observable) -> bool:
        """Check if this observable commutes with another.

        Two Pauli strings commute if they differ on an even number of
        qubits (excluding positions where either is identity).
        """
        if self.n_qubits != other.n_qubits:
            raise ValueError(
                f"Cannot compare observables with different qubit counts: "
                f"{self.n_qubits} vs {other.n_qubits}"
            )

        anticommute_count = 0
        for p1, p2 in zip(self.pauli_string, other.pauli_string, strict=False):
            if p1 != "I" and p2 != "I" and p1 != p2:
                anticommute_count += 1

        return anticommute_count % 2 == 0

    def shared_basis(self, other: Observable) -> str | None:
        """Get shared measurement basis if observables commute qubit-wise.

        Returns None if no shared basis exists (observables don't commute
        qubit-wise, though they may still commute globally).
        """
        if self.n_qubits != other.n_qubits:
            return None

        basis = []
        for p1, p2 in zip(self.pauli_string, other.pauli_string, strict=False):
            if p1 == "I":
                basis.append(p2 if p2 != "I" else "Z")  # Default to Z
            elif p2 == "I":
                basis.append(p1)
            elif p1 == p2:
                basis.append(p1)
            else:
                return None  # Conflict on this qubit

        return "".join(basis)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "observable_id": self.observable_id,
            "pauli_string": self.pauli_string,
            "coefficient": self.coefficient,
            "observable_type": self.observable_type.value,
            "locality": self.locality,
            "n_qubits": self.n_qubits,
            "group_id": self.group_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Observable:
        """Create from dictionary."""
        return cls(
            pauli_string=data["pauli_string"],
            coefficient=data.get("coefficient", 1.0),
            observable_id=data.get("observable_id"),
            group_id=data.get("group_id"),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """String representation."""
        if self.coefficient == 1.0:
            return self.pauli_string
        return f"{self.coefficient}*{self.pauli_string}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"Observable('{self.pauli_string}', coef={self.coefficient}, id={self.observable_id})"
        )

    def __hash__(self) -> int:
        """Hash based on Pauli string and coefficient."""
        return hash((self.pauli_string, self.coefficient))

    def __eq__(self, other: object) -> bool:
        """Equality based on Pauli string and coefficient."""
        if not isinstance(other, Observable):
            return False
        return self.pauli_string == other.pauli_string and np.isclose(
            self.coefficient, other.coefficient
        )


@dataclass
class ObservableSet:
    """A set of observables with generation metadata (§3.3).

    This class represents a collection of observables to be estimated,
    along with metadata about how they were generated for reproducibility.

    Attributes:
        observables: List of Observable objects.
        observable_set_id: Unique identifier for this set.
        generator_id: ID of the generator that created this set.
        generator_version: Version of the generator.
        generator_seed: Random seed used for generation.
        generator_params: Parameters passed to the generator.
        n_qubits: Number of qubits (all observables must match).
        metadata: Additional set-level metadata.
    """

    observables: list[Observable]
    observable_set_id: str | None = None
    generator_id: str | None = None
    generator_version: str | None = None
    generator_seed: int | None = None
    generator_params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and set defaults."""
        if not self.observables:
            raise ValueError("ObservableSet must contain at least one observable")

        # Verify all observables have same qubit count
        n_qubits_set = {obs.n_qubits for obs in self.observables}
        if len(n_qubits_set) > 1:
            raise ValueError(f"All observables must have same qubit count, got: {n_qubits_set}")

        # Auto-generate set ID if not provided
        if self.observable_set_id is None:
            self.observable_set_id = f"obsset_{uuid.uuid4().hex[:8]}"

    @property
    def n_qubits(self) -> int:
        """Number of qubits for observables in this set."""
        return self.observables[0].n_qubits

    @property
    def n_observables(self) -> int:
        """Number of observables in this set."""
        return len(self.observables)

    @property
    def M(self) -> int:
        """Alias for n_observables (common notation)."""
        return self.n_observables

    def get_by_id(self, observable_id: str) -> Observable:
        """Get an observable by its ID."""
        for obs in self.observables:
            if obs.observable_id == observable_id:
                return obs
        raise KeyError(f"Observable with ID '{observable_id}' not found")

    def locality_distribution(self) -> dict[int, int]:
        """Get distribution of Pauli weights."""
        dist: dict[int, int] = {}
        for obs in self.observables:
            dist[obs.locality] = dist.get(obs.locality, 0) + 1
        return dict(sorted(dist.items()))

    def max_locality(self) -> int:
        """Maximum Pauli weight in the set."""
        return max(obs.locality for obs in self.observables)

    def mean_locality(self) -> float:
        """Mean Pauli weight in the set."""
        return sum(obs.locality for obs in self.observables) / len(self.observables)

    def __iter__(self) -> Iterator[Observable]:
        """Iterate over observables."""
        return iter(self.observables)

    def __len__(self) -> int:
        """Number of observables."""
        return len(self.observables)

    def __getitem__(self, index: int) -> Observable:
        """Get observable by index."""
        return self.observables[index]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "observable_set_id": self.observable_set_id,
            "n_observables": self.n_observables,
            "n_qubits": self.n_qubits,
            "generator_id": self.generator_id,
            "generator_version": self.generator_version,
            "generator_seed": self.generator_seed,
            "generator_params": self.generator_params,
            "observables": [obs.to_dict() for obs in self.observables],
            "locality_distribution": self.locality_distribution(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ObservableSet:
        """Create from dictionary."""
        observables = [Observable.from_dict(obs_data) for obs_data in data["observables"]]
        return cls(
            observables=observables,
            observable_set_id=data.get("observable_set_id"),
            generator_id=data.get("generator_id"),
            generator_version=data.get("generator_version"),
            generator_seed=data.get("generator_seed"),
            generator_params=data.get("generator_params", {}),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_pauli_strings(
        cls,
        pauli_strings: list[str],
        coefficients: list[float] | None = None,
        **kwargs: Any,
    ) -> ObservableSet:
        """Create from a list of Pauli strings.

        Args:
            pauli_strings: List of Pauli string representations.
            coefficients: Optional list of coefficients (default all 1.0).
            **kwargs: Additional arguments passed to ObservableSet.

        Returns:
            ObservableSet containing the specified observables.
        """
        if coefficients is None:
            coefficients = [1.0] * len(pauli_strings)
        elif len(coefficients) != len(pauli_strings):
            raise ValueError(
                f"Number of coefficients ({len(coefficients)}) must match "
                f"number of Pauli strings ({len(pauli_strings)})"
            )

        observables = [
            Observable(pauli_string=ps, coefficient=coef)
            for ps, coef in zip(pauli_strings, coefficients, strict=False)
        ]
        return cls(observables=observables, **kwargs)
