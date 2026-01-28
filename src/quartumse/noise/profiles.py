"""Canonical noise profiles (Measurements Bible §9.4).

This module defines the standard library of noise profiles required
for benchmarking under realistic conditions.

Required profiles:
1. ideal - No noise
2. readout_bitflip(p) - Readout errors with p in {1e-3, 1e-2, 5e-2}
3. depolarizing(p1, p2) - Gate errors with various (p1, p2) pairs
4. amplitude_phase_damping(T1, T2, dt) - Coherent errors (optional)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class NoiseType(str, Enum):
    """Types of noise models."""

    IDEAL = "ideal"
    READOUT_BITFLIP = "readout_bitflip"
    DEPOLARIZING = "depolarizing"
    AMPLITUDE_DAMPING = "amplitude_damping"
    PHASE_DAMPING = "phase_damping"
    THERMAL_RELAXATION = "thermal_relaxation"
    CUSTOM = "custom"


@dataclass
class NoiseProfile:
    """A noise profile specification.

    Attributes:
        profile_id: Unique identifier for this profile.
        noise_type: Type of noise model.
        parameters: Noise model parameters.
        description: Human-readable description.
        metadata: Additional metadata.
    """

    profile_id: str
    noise_type: NoiseType
    parameters: dict[str, float] = field(default_factory=dict)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "profile_id": self.profile_id,
            "noise_type": self.noise_type.value,
            "parameters": self.parameters,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NoiseProfile:
        """Create from dictionary."""
        return cls(
            profile_id=data["profile_id"],
            noise_type=NoiseType(data["noise_type"]),
            parameters=data.get("parameters", {}),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# Canonical noise profiles (§9.4)
# ============================================================================

IDEAL_PROFILE = NoiseProfile(
    profile_id="ideal",
    noise_type=NoiseType.IDEAL,
    parameters={},
    description="No noise (ideal simulation)",
)

# Readout bitflip profiles
READOUT_PROFILES = {
    "readout_1e-3": NoiseProfile(
        profile_id="readout_1e-3",
        noise_type=NoiseType.READOUT_BITFLIP,
        parameters={"p": 1e-3},
        description="Readout bitflip with p=0.001",
    ),
    "readout_1e-2": NoiseProfile(
        profile_id="readout_1e-2",
        noise_type=NoiseType.READOUT_BITFLIP,
        parameters={"p": 1e-2},
        description="Readout bitflip with p=0.01",
    ),
    "readout_5e-2": NoiseProfile(
        profile_id="readout_5e-2",
        noise_type=NoiseType.READOUT_BITFLIP,
        parameters={"p": 5e-2},
        description="Readout bitflip with p=0.05",
    ),
}

# Depolarizing profiles (p1 = 1-qubit, p2 = 2-qubit)
DEPOLARIZING_PROFILES = {
    "depol_low": NoiseProfile(
        profile_id="depol_low",
        noise_type=NoiseType.DEPOLARIZING,
        parameters={"p1": 1e-4, "p2": 1e-3},
        description="Low depolarizing noise (p1=1e-4, p2=1e-3)",
    ),
    "depol_medium": NoiseProfile(
        profile_id="depol_medium",
        noise_type=NoiseType.DEPOLARIZING,
        parameters={"p1": 1e-3, "p2": 1e-2},
        description="Medium depolarizing noise (p1=1e-3, p2=1e-2)",
    ),
    "depol_high": NoiseProfile(
        profile_id="depol_high",
        noise_type=NoiseType.DEPOLARIZING,
        parameters={"p1": 1e-2, "p2": 5e-2},
        description="High depolarizing noise (p1=1e-2, p2=5e-2)",
    ),
}

# Thermal relaxation profiles
THERMAL_PROFILES = {
    "thermal_ibm_typical": NoiseProfile(
        profile_id="thermal_ibm_typical",
        noise_type=NoiseType.THERMAL_RELAXATION,
        parameters={"T1_us": 100, "T2_us": 80, "gate_time_ns": 35},
        description="Typical IBM quantum parameters",
    ),
}

# All canonical profiles
CANONICAL_PROFILES: dict[str, NoiseProfile] = {
    "ideal": IDEAL_PROFILE,
    **READOUT_PROFILES,
    **DEPOLARIZING_PROFILES,
    **THERMAL_PROFILES,
}


def get_profile(profile_id: str) -> NoiseProfile:
    """Get a noise profile by ID.

    Args:
        profile_id: Profile identifier.

    Returns:
        NoiseProfile object.

    Raises:
        KeyError: If profile not found.
    """
    if profile_id not in CANONICAL_PROFILES:
        raise KeyError(
            f"Unknown noise profile: {profile_id}. "
            f"Available: {list(CANONICAL_PROFILES.keys())}"
        )
    return CANONICAL_PROFILES[profile_id]


def list_profiles() -> list[str]:
    """List available noise profile IDs."""
    return list(CANONICAL_PROFILES.keys())


def register_profile(profile: NoiseProfile) -> None:
    """Register a custom noise profile.

    Args:
        profile: NoiseProfile to register.
    """
    CANONICAL_PROFILES[profile.profile_id] = profile


# ============================================================================
# Noise application utilities
# ============================================================================


def apply_readout_noise(
    bitstring: str,
    p: float,
    rng: np.random.Generator | None = None,
) -> str:
    """Apply readout bitflip noise to a bitstring.

    Each bit is flipped with probability p.

    Args:
        bitstring: Original measurement outcome.
        p: Bitflip probability.
        rng: Random number generator.

    Returns:
        Noisy bitstring.
    """
    if rng is None:
        rng = np.random.default_rng()

    result = []
    for bit in bitstring:
        if rng.random() < p:
            result.append("1" if bit == "0" else "0")
        else:
            result.append(bit)

    return "".join(result)


def apply_readout_noise_batch(
    bitstrings: list[str],
    p: float,
    seed: int | None = None,
) -> list[str]:
    """Apply readout noise to a batch of bitstrings.

    Args:
        bitstrings: List of measurement outcomes.
        p: Bitflip probability.
        seed: Random seed.

    Returns:
        List of noisy bitstrings.
    """
    rng = np.random.default_rng(seed)
    return [apply_readout_noise(bs, p, rng) for bs in bitstrings]


class NoiseModel(ABC):
    """Abstract base class for noise models.

    Noise models can be applied to simulation backends to add
    realistic noise effects.
    """

    @abstractmethod
    def apply_to_counts(
        self,
        counts: dict[str, int],
        n_qubits: int,
        seed: int | None = None,
    ) -> dict[str, int]:
        """Apply noise to measurement counts.

        Args:
            counts: Original measurement counts.
            n_qubits: Number of qubits.
            seed: Random seed.

        Returns:
            Noisy measurement counts.
        """
        pass

    @abstractmethod
    def get_profile(self) -> NoiseProfile:
        """Get the noise profile for this model."""
        pass


class ReadoutNoiseModel(NoiseModel):
    """Readout bitflip noise model.

    Applies symmetric bitflip noise to measurement outcomes.
    """

    def __init__(self, p: float) -> None:
        """Initialize with bitflip probability.

        Args:
            p: Probability of flipping each bit.
        """
        self.p = p

    def apply_to_counts(
        self,
        counts: dict[str, int],
        n_qubits: int,
        seed: int | None = None,
    ) -> dict[str, int]:
        """Apply readout noise to counts."""
        rng = np.random.default_rng(seed)

        # Expand counts to bitstrings
        bitstrings = []
        for bs, count in counts.items():
            bitstrings.extend([bs] * count)

        # Apply noise
        noisy_bitstrings = [apply_readout_noise(bs, self.p, rng) for bs in bitstrings]

        # Re-aggregate
        noisy_counts: dict[str, int] = {}
        for bs in noisy_bitstrings:
            noisy_counts[bs] = noisy_counts.get(bs, 0) + 1

        return noisy_counts

    def get_profile(self) -> NoiseProfile:
        """Get noise profile."""
        return NoiseProfile(
            profile_id=f"readout_{self.p}",
            noise_type=NoiseType.READOUT_BITFLIP,
            parameters={"p": self.p},
        )


class DepolarizingNoiseModel(NoiseModel):
    """Depolarizing noise model.

    Applies depolarizing noise based on circuit structure.
    This is a simplified model that affects measurement outcomes
    based on circuit depth and gate counts.
    """

    def __init__(self, p1: float, p2: float) -> None:
        """Initialize with error probabilities.

        Args:
            p1: Single-qubit gate error probability.
            p2: Two-qubit gate error probability.
        """
        self.p1 = p1
        self.p2 = p2

    def apply_to_counts(
        self,
        counts: dict[str, int],
        n_qubits: int,
        seed: int | None = None,
        n_1q_gates: int = 0,
        n_2q_gates: int = 0,
    ) -> dict[str, int]:
        """Apply depolarizing noise to counts.

        This is a simplified model that applies an effective
        error rate based on gate counts.
        """
        # Compute effective error probability
        # p_eff ≈ 1 - (1-p1)^n1 * (1-p2)^n2
        p_eff = 1 - ((1 - self.p1) ** n_1q_gates) * ((1 - self.p2) ** n_2q_gates)

        # Apply as readout-like noise (simplified)
        rng = np.random.default_rng(seed)

        noisy_counts: dict[str, int] = {}
        for bs, count in counts.items():
            for _ in range(count):
                # With probability p_eff, randomize some bits
                if rng.random() < p_eff:
                    # Flip a random subset of bits
                    n_flips = rng.integers(1, max(2, n_qubits // 2))
                    flip_positions = rng.choice(n_qubits, size=n_flips, replace=False)
                    bs_list = list(bs)
                    for pos in flip_positions:
                        bs_list[pos] = "1" if bs_list[pos] == "0" else "0"
                    noisy_bs = "".join(bs_list)
                else:
                    noisy_bs = bs

                noisy_counts[noisy_bs] = noisy_counts.get(noisy_bs, 0) + 1

        return noisy_counts

    def get_profile(self) -> NoiseProfile:
        """Get noise profile."""
        return NoiseProfile(
            profile_id=f"depol_p1{self.p1}_p2{self.p2}",
            noise_type=NoiseType.DEPOLARIZING,
            parameters={"p1": self.p1, "p2": self.p2},
        )


def create_noise_model(profile: NoiseProfile) -> NoiseModel:
    """Create a noise model from a profile.

    Args:
        profile: Noise profile specification.

    Returns:
        NoiseModel instance.

    Raises:
        ValueError: If noise type is not supported.
    """
    if profile.noise_type == NoiseType.IDEAL:
        # Return identity model
        class IdealNoiseModel(NoiseModel):
            def apply_to_counts(self, counts, n_qubits, seed=None):
                return counts

            def get_profile(self):
                return IDEAL_PROFILE

        return IdealNoiseModel()

    elif profile.noise_type == NoiseType.READOUT_BITFLIP:
        return ReadoutNoiseModel(p=profile.parameters["p"])

    elif profile.noise_type == NoiseType.DEPOLARIZING:
        return DepolarizingNoiseModel(
            p1=profile.parameters["p1"],
            p2=profile.parameters["p2"],
        )

    else:
        raise ValueError(f"Unsupported noise type: {profile.noise_type}")
