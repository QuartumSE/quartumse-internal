"""Unit tests for classical shadows v0 implementation."""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from quartumse.shadows.config import ShadowConfig
from quartumse.shadows.core import Observable
from quartumse.shadows.v0_baseline import RandomLocalCliffordShadows


class TestRandomLocalCliffordShadows:
    """Test baseline classical shadows implementation."""

    def test_initialization(self, shadow_config):
        """Test shadow implementation initializes correctly."""
        shadows = RandomLocalCliffordShadows(shadow_config)
        assert shadows.config == shadow_config
        assert shadows.rng is not None
        assert shadows.inverse_channel is not None

    def test_generate_measurement_circuits(self, shadow_config, ghz_circuit_3q):
        """Test generation of shadow measurement circuits."""
        shadows = RandomLocalCliffordShadows(shadow_config)
        num_shadows = 10

        circuits = shadows.generate_measurement_circuits(ghz_circuit_3q, num_shadows)

        assert len(circuits) == num_shadows
        assert all(isinstance(c, QuantumCircuit) for c in circuits)
        assert shadows.measurement_bases is not None
        assert shadows.measurement_bases.shape == (num_shadows, 3)

    def test_variance_bound(self, shadow_config):
        """Test variance bound calculation."""
        shadows = RandomLocalCliffordShadows(shadow_config)

        # Single-qubit observable (support=1): variance ≤ 4/M
        obs1 = Observable("ZII", coefficient=1.0)
        bound1 = shadows.compute_variance_bound(obs1, shadow_size=100)
        assert bound1 == pytest.approx(4.0 / 100)

        # Two-qubit observable (support=2): variance ≤ 16/M
        obs2 = Observable("ZZI", coefficient=1.0)
        bound2 = shadows.compute_variance_bound(obs2, shadow_size=100)
        assert bound2 == pytest.approx(16.0 / 100)

    def test_estimate_shadow_size_needed(self, shadow_config):
        """Test shadow size estimation for target precision."""
        shadows = RandomLocalCliffordShadows(shadow_config)

        obs = Observable("ZII", coefficient=1.0)
        target_precision = 0.1
        confidence = 0.95

        shadow_size = shadows.estimate_shadow_size_needed(obs, target_precision, confidence)

        assert shadow_size > 0
        assert isinstance(shadow_size, int)

    def test_pauli_string_support_counting(self, shadow_config):
        """Test that support size is computed correctly."""
        shadows = RandomLocalCliffordShadows(shadow_config)

        obs_support_0 = Observable("III", coefficient=1.0)
        obs_support_1 = Observable("ZII", coefficient=1.0)
        obs_support_2 = Observable("ZZI", coefficient=1.0)
        obs_support_3 = Observable("XYZ", coefficient=1.0)

        # Support size should affect variance bound
        bound0 = shadows.compute_variance_bound(obs_support_0, 100)
        bound1 = shadows.compute_variance_bound(obs_support_1, 100)
        bound2 = shadows.compute_variance_bound(obs_support_2, 100)
        bound3 = shadows.compute_variance_bound(obs_support_3, 100)

        assert bound0 == pytest.approx(1.0 / 100)  # 4^0 / 100
        assert bound1 == pytest.approx(4.0 / 100)  # 4^1 / 100
        assert bound2 == pytest.approx(16.0 / 100)  # 4^2 / 100
        assert bound3 == pytest.approx(64.0 / 100)  # 4^3 / 100

    @pytest.mark.slow
    def test_estimate_observable_on_ghz(self, shadow_config, ghz_circuit_3q, backend):
        """Test observable estimation on GHZ state."""
        shadow_config.shadow_size = 500  # Increase for better statistics
        shadows = RandomLocalCliffordShadows(shadow_config)

        # Generate shadow circuits
        circuits = shadows.generate_measurement_circuits(ghz_circuit_3q, shadow_config.shadow_size)

        # Execute (each circuit gets 1 shot)
        from qiskit import transpile

        transpiled = transpile(circuits, backend=backend)
        job = backend.run(transpiled, shots=1)
        result = job.result()

        # Extract outcomes
        outcomes = []
        for i in range(shadow_config.shadow_size):
            counts = result.get_counts(i)
            bitstring = list(counts.keys())[0]
            outcome = np.array([int(b) for b in bitstring[::-1]])
            outcomes.append(outcome)

        outcomes = np.array(outcomes)

        # Reconstruct shadows
        shadows.reconstruct_classical_shadow(outcomes, shadows.measurement_bases)

        # Test estimation
        obs_z0 = Observable("ZII", coefficient=1.0)
        estimate = shadows.estimate_observable(obs_z0)

        # For GHZ: ⟨Z_0⟩ = 0 (superposition)
        # Allow some deviation due to sampling
        assert abs(estimate.expectation_value) < 0.2  # Loose bound
        assert estimate.confidence_interval is not None
        assert estimate.shadow_size == shadow_config.shadow_size
