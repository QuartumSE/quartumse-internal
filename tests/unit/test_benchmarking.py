"""Unit tests for benchmarking module."""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from quartumse.benchmarking import (
    quick_comparison,
    compute_ssf,
    simulate_protocol_execution,
)
from quartumse.protocols import (
    DirectNaiveProtocol,
    DirectGroupedProtocol,
    ShadowsV0Protocol,
)
from quartumse.observables import Observable, ObservableSet


@pytest.fixture
def bell_obs_set():
    """Observable set for Bell state testing."""
    obs_list = [
        Observable(observable_id="z0", pauli_string="ZI", coefficient=1.0),
        Observable(observable_id="z1", pauli_string="IZ", coefficient=1.0),
        Observable(observable_id="zz", pauli_string="ZZ", coefficient=1.0),
        Observable(observable_id="xx", pauli_string="XX", coefficient=1.0),
    ]
    return ObservableSet(observables=obs_list)


@pytest.fixture
def ground_truth_bell():
    """Ground truth for Bell state observables."""
    return {
        "z0": 0.0,
        "z1": 0.0,
        "zz": 1.0,
        "xx": 1.0,
    }


class TestSimulateProtocolExecution:
    """Test simulate_protocol_execution function."""

    def test_direct_naive_protocol(self, bell_obs_set, ground_truth_bell):
        """Test simulation with DirectNaiveProtocol."""
        protocol = DirectNaiveProtocol()

        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=bell_obs_set,
            n_shots=100,
            seed=42,
            true_expectations=ground_truth_bell,
        )

        assert estimates is not None
        assert len(estimates.estimates) == 4
        assert estimates.total_shots > 0

        for est in estimates.estimates:
            assert est.observable_id in ground_truth_bell
            assert est.se >= 0
            assert -1 <= est.estimate <= 1

    def test_direct_grouped_protocol(self, bell_obs_set, ground_truth_bell):
        """Test simulation with DirectGroupedProtocol."""
        protocol = DirectGroupedProtocol()

        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=bell_obs_set,
            n_shots=100,
            seed=42,
            true_expectations=ground_truth_bell,
        )

        assert estimates is not None
        assert len(estimates.estimates) == 4

    def test_shadows_v0_protocol(self, bell_obs_set, ground_truth_bell):
        """Test simulation with ShadowsV0Protocol."""
        protocol = ShadowsV0Protocol()

        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=bell_obs_set,
            n_shots=100,
            seed=42,
            true_expectations=ground_truth_bell,
        )

        assert estimates is not None
        assert len(estimates.estimates) == 4
        assert estimates.protocol_id == "classical_shadows_v0"

    def test_reproducibility_with_seed(self, bell_obs_set, ground_truth_bell):
        """Test that same seed produces same results."""
        protocol = DirectNaiveProtocol()

        est1 = simulate_protocol_execution(
            protocol=protocol,
            observable_set=bell_obs_set,
            n_shots=100,
            seed=42,
            true_expectations=ground_truth_bell,
        )

        est2 = simulate_protocol_execution(
            protocol=protocol,
            observable_set=bell_obs_set,
            n_shots=100,
            seed=42,
            true_expectations=ground_truth_bell,
        )

        # Same seed should produce identical estimates
        for e1, e2 in zip(est1.estimates, est2.estimates):
            assert e1.estimate == e2.estimate
            assert e1.se == e2.se


class TestComputeSSF:
    """Test Shot-Savings Factor computation."""

    def test_ssf_computation(self, bell_obs_set, ground_truth_bell):
        """Test SSF computation from protocol results."""
        # Run protocols
        protocols = [DirectGroupedProtocol(), ShadowsV0Protocol()]

        results = quick_comparison(
            protocols=protocols,
            observable_set=bell_obs_set,
            n_shots=200,
            true_expectations=ground_truth_bell,
            seed=42,
        )

        # Compute SSF with direct_grouped as baseline
        ssf_dict = compute_ssf(results, baseline_id="direct_grouped")

        assert "direct_grouped" in ssf_dict
        assert "classical_shadows_v0" in ssf_dict
        assert ssf_dict["direct_grouped"] == pytest.approx(1.0)  # Baseline SSF = 1

    def test_ssf_baseline_not_found(self, bell_obs_set, ground_truth_bell):
        """Test SSF raises error when baseline not found."""
        protocols = [DirectGroupedProtocol()]

        results = quick_comparison(
            protocols=protocols,
            observable_set=bell_obs_set,
            n_shots=100,
            true_expectations=ground_truth_bell,
            seed=42,
        )

        with pytest.raises(ValueError, match="Baseline protocol"):
            compute_ssf(results, baseline_id="nonexistent_protocol")


class TestQuickComparison:
    """Test quick_comparison function."""

    def test_quick_comparison_returns_results(self, bell_obs_set, ground_truth_bell):
        """Test quick_comparison produces valid results."""
        protocols = [DirectNaiveProtocol(), DirectGroupedProtocol()]

        results = quick_comparison(
            protocols=protocols,
            observable_set=bell_obs_set,
            n_shots=100,
            true_expectations=ground_truth_bell,
            seed=42,
        )

        assert len(results) == 2
        for protocol_id, estimates in results.items():
            assert estimates is not None
            assert len(estimates.estimates) == 4

    def test_quick_comparison_with_shadows(self, bell_obs_set, ground_truth_bell):
        """Test quick_comparison includes shadows protocol."""
        protocols = [DirectGroupedProtocol(), ShadowsV0Protocol()]

        results = quick_comparison(
            protocols=protocols,
            observable_set=bell_obs_set,
            n_shots=100,
            true_expectations=ground_truth_bell,
            seed=42,
        )

        assert "direct_grouped" in results
        assert "classical_shadows_v0" in results


class TestBenchmarkingMetrics:
    """Test metric computation from benchmark results."""

    def test_error_can_be_computed(self, bell_obs_set, ground_truth_bell):
        """Test that error metrics can be computed from estimates."""
        protocol = DirectNaiveProtocol()

        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=bell_obs_set,
            n_shots=100,
            seed=42,
            true_expectations=ground_truth_bell,
        )

        # Verify we can compute errors
        errors = []
        for est in estimates.estimates:
            true_val = ground_truth_bell[est.observable_id]
            error = abs(est.estimate - true_val)
            errors.append(error)

        # Verify errors are valid floats
        mean_error = np.mean(errors)
        assert np.isfinite(mean_error)
        assert mean_error >= 0

    def test_worst_case_error_computation(self, bell_obs_set, ground_truth_bell):
        """Test that worst-case error can be computed."""
        protocol = DirectNaiveProtocol()

        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=bell_obs_set,
            n_shots=100,
            seed=42,
            true_expectations=ground_truth_bell,
        )

        # Find worst-case error
        max_error = 0.0
        for est in estimates.estimates:
            true_val = ground_truth_bell[est.observable_id]
            error = abs(est.estimate - true_val)
            max_error = max(max_error, error)

        # Verify worst-case error is valid
        assert np.isfinite(max_error)
        assert max_error >= 0
        # Estimates should be in [-1, 1], so max error <= 2
        assert max_error <= 2.0


class TestBenchmarkReproducibility:
    """Test reproducibility of benchmark results."""

    def test_multiple_replicates_vary(self, bell_obs_set, ground_truth_bell):
        """Test that different seeds produce different results."""
        protocol = DirectNaiveProtocol()

        results = []
        for seed in [42, 43, 44]:
            est = simulate_protocol_execution(
                protocol=protocol,
                observable_set=bell_obs_set,
                n_shots=100,
                seed=seed,
                true_expectations=ground_truth_bell,
            )
            results.append([e.estimate for e in est.estimates])

        # Different seeds should give (slightly) different estimates
        assert results[0] != results[1]
        assert results[1] != results[2]

    @pytest.mark.slow
    def test_variance_decreases_with_shots(self, bell_obs_set, ground_truth_bell):
        """Test that variance decreases with more shots."""
        protocol = DirectNaiveProtocol()

        def get_se_for_shots(n_shots, n_replicates=5):
            ses = []
            for rep in range(n_replicates):
                est = simulate_protocol_execution(
                    protocol=protocol,
                    observable_set=bell_obs_set,
                    n_shots=n_shots,
                    seed=42 + rep * 100,
                    true_expectations=ground_truth_bell,
                )
                ses.extend([e.se for e in est.estimates])
            return np.mean(ses)

        se_100 = get_se_for_shots(100)
        se_400 = get_se_for_shots(400)

        # SE should scale as 1/sqrt(N), so 4x shots -> ~0.5x SE
        assert se_400 < se_100
        assert se_400 < se_100 * 0.7  # Should be approximately half
