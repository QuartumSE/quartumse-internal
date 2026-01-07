"""Backend infrastructure for quantum simulation and ground truth computation.

This module provides:
- StatevectorBackend: Exact ground truth computation via statevector simulation
- NoisyBackend: Noisy simulation for noise sensitivity studies
- SamplerBackend: Shot-based sampling for protocol execution

Ground truth is critical for publication-grade benchmarking (Measurements Bible §3.4).
"""

from quartumse.backends.truth import (
    GroundTruthConfig,
    StatevectorBackend,
    compute_ground_truth,
    compute_observable_expectation,
)
from quartumse.backends.sampler import (
    IdealSampler,
    NoisySampler,
    sample_circuit,
)

__all__ = [
    # Ground truth
    "GroundTruthConfig",
    "StatevectorBackend",
    "compute_ground_truth",
    "compute_observable_expectation",
    # Sampling
    "IdealSampler",
    "NoisySampler",
    "sample_circuit",
]
