"""Noise profiles and hardware tracking (Measurements Bible §9.4, §9.5).

This package provides:
- Canonical noise profiles for benchmarking
- Noise models for simulation
- Hardware execution tracking and calibration drift detection

Usage:
    from quartumse.noise import (
        # Noise profiles
        NoiseProfile,
        NoiseType,
        get_profile,
        list_profiles,
        CANONICAL_PROFILES,
        # Noise models
        NoiseModel,
        ReadoutNoiseModel,
        DepolarizingNoiseModel,
        create_noise_model,
        # Hardware tracking
        JobMetadata,
        JobStatus,
        CalibrationData,
        CompilationInfo,
        HardwareSession,
        HardwareTracker,
    )

    # Get a canonical noise profile
    profile = get_profile("readout_1e-2")

    # Create noise model
    model = create_noise_model(profile)
    noisy_counts = model.apply_to_counts(counts, n_qubits=4)

    # Track hardware execution
    tracker = HardwareTracker()
    session = tracker.start_session("session_1", "ibm_brisbane")
    tracker.add_job(job_metadata)
    tracker.end_session()
"""

from .hardware import (
    CalibrationData,
    CompilationInfo,
    HardwareSession,
    HardwareTracker,
    JobMetadata,
    JobStatus,
)
from .profiles import (
    CANONICAL_PROFILES,
    DepolarizingNoiseModel,
    NoiseModel,
    NoiseProfile,
    NoiseType,
    ReadoutNoiseModel,
    apply_readout_noise,
    apply_readout_noise_batch,
    create_noise_model,
    get_profile,
    list_profiles,
    register_profile,
)

__all__ = [
    # Noise profiles
    "NoiseProfile",
    "NoiseType",
    "CANONICAL_PROFILES",
    "get_profile",
    "list_profiles",
    "register_profile",
    # Noise models
    "NoiseModel",
    "ReadoutNoiseModel",
    "DepolarizingNoiseModel",
    "create_noise_model",
    "apply_readout_noise",
    "apply_readout_noise_batch",
    # Hardware tracking
    "JobStatus",
    "JobMetadata",
    "CalibrationData",
    "CompilationInfo",
    "HardwareSession",
    "HardwareTracker",
]
