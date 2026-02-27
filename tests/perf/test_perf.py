"""Performance regression tests.

Each test times a hot-path function and compares against committed baselines.
Regressions >30% fail on Linux CI; on other platforms they warn only.

Run:  pytest tests/perf/ -v -m perf
Update baselines:  python scripts/update_perf_baseline.py
"""

from __future__ import annotations

import statistics
import sys
import time
import warnings

import numpy as np
import pytest

N_SHOTS = 1000
SEED = 42
REGRESSION_THRESHOLD = 0.30  # 30%


def run_timed(fn, *, n_runs: int = 7) -> list[float]:
    """Call fn n_runs times and return list of elapsed seconds."""
    times: list[float] = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return times


def assert_no_regression(
    benchmark_name: str,
    times: list[float],
    baseline: dict,
    threshold: float = REGRESSION_THRESHOLD,
) -> None:
    """Assert median timing has not regressed beyond threshold."""
    enforce = sys.platform == "linux"
    median = statistics.median(times)
    baseline_benchmarks = baseline.get("benchmarks", {})

    if benchmark_name not in baseline_benchmarks:
        pytest.skip(f"No baseline for {benchmark_name!r} — run update_perf_baseline.py")

    baseline_median = baseline_benchmarks[benchmark_name]["median"]
    allowed = baseline_median * (1 + threshold)
    regressed = median > allowed

    msg = (
        f"{benchmark_name}: median={median:.4f}s vs baseline={baseline_median:.4f}s "
        f"(allowed={allowed:.4f}s, threshold={threshold:.0%})"
    )

    if regressed and enforce:
        pytest.fail(f"Performance regression: {msg}")
    elif regressed:
        warnings.warn(f"Performance regression (non-Linux, not enforced): {msg}", stacklevel=2)


@pytest.mark.perf
def test_simulate_direct_naive(perf_workload, perf_baseline):
    """Time DirectNaiveProtocol end-to-end simulation."""
    from quartumse.benchmarking import simulate_protocol_execution
    from quartumse.protocols import DirectNaiveProtocol

    w = perf_workload
    proto = DirectNaiveProtocol()

    def run():
        simulate_protocol_execution(
            protocol=proto,
            observable_set=w["obs_set"],
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=w["ground_truth"],
            circuit=w["circuit"],
        )

    times = run_timed(run, n_runs=7)
    assert_no_regression("simulate_direct_naive", times, perf_baseline)


@pytest.mark.perf
def test_simulate_direct_grouped(perf_workload, perf_baseline):
    """Time DirectGroupedProtocol end-to-end simulation."""
    from quartumse.benchmarking import simulate_protocol_execution
    from quartumse.protocols import DirectGroupedProtocol

    w = perf_workload
    proto = DirectGroupedProtocol()

    def run():
        simulate_protocol_execution(
            protocol=proto,
            observable_set=w["obs_set"],
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=w["ground_truth"],
            circuit=w["circuit"],
        )

    times = run_timed(run, n_runs=7)
    assert_no_regression("simulate_direct_grouped", times, perf_baseline)


@pytest.mark.perf
def test_simulate_direct_optimized(perf_workload, perf_baseline):
    """Time DirectOptimizedProtocol end-to-end simulation."""
    from quartumse.benchmarking import simulate_protocol_execution
    from quartumse.protocols import DirectOptimizedProtocol

    w = perf_workload
    proto = DirectOptimizedProtocol()

    def run():
        simulate_protocol_execution(
            protocol=proto,
            observable_set=w["obs_set"],
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=w["ground_truth"],
            circuit=w["circuit"],
        )

    times = run_timed(run, n_runs=7)
    assert_no_regression("simulate_direct_optimized", times, perf_baseline)


@pytest.mark.perf
def test_simulate_shadows_v0(perf_workload, perf_baseline):
    """Time ShadowsV0Protocol end-to-end simulation."""
    from quartumse.benchmarking import simulate_protocol_execution
    from quartumse.protocols import ShadowsV0Protocol

    w = perf_workload
    proto = ShadowsV0Protocol()

    def run():
        simulate_protocol_execution(
            protocol=proto,
            observable_set=w["obs_set"],
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=w["ground_truth"],
            circuit=w["circuit"],
        )

    times = run_timed(run, n_runs=7)
    assert_no_regression("simulate_shadows_v0", times, perf_baseline)


@pytest.mark.perf
def test_observable_set_construction(perf_workload, perf_baseline):
    """Time ObservableSet construction with 20 observables on 4 qubits."""
    from quartumse.observables import Observable, ObservableSet

    paulis_raw = perf_workload["paulis_raw"]

    def run():
        obs_list = [
            Observable(observable_id=f"o{i:02d}", pauli_string=ps, coefficient=1.0)
            for i, ps in enumerate(paulis_raw)
        ]
        _ = ObservableSet(observables=obs_list)

    times = run_timed(run, n_runs=7)
    assert_no_regression("observable_set_construction", times, perf_baseline)


@pytest.mark.perf
def test_grouping_algorithms(perf_workload, perf_baseline):
    """Time greedy_grouping + sorted_insertion_grouping."""
    from quartumse.observables.grouping import greedy_grouping, sorted_insertion_grouping

    obs = perf_workload["obs_set"].observables

    def run():
        greedy_grouping(obs)
        sorted_insertion_grouping(obs)

    times = run_timed(run, n_runs=7)
    assert_no_regression("grouping_algorithms", times, perf_baseline)


@pytest.mark.perf
def test_quick_comparison_3proto(perf_workload, perf_baseline):
    """Time quick_comparison with 3 protocols end-to-end."""
    from quartumse.benchmarking import quick_comparison
    from quartumse.protocols import (
        DirectGroupedProtocol,
        DirectNaiveProtocol,
        ShadowsV0Protocol,
    )

    w = perf_workload
    protos = [DirectNaiveProtocol(), DirectGroupedProtocol(), ShadowsV0Protocol()]

    def run():
        quick_comparison(
            observable_set=w["obs_set"],
            protocols=protos,
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=w["ground_truth"],
        )

    times = run_timed(run, n_runs=7)
    assert_no_regression("quick_comparison_3proto", times, perf_baseline)


@pytest.mark.perf
def test_eigenvalue_direct_naive(perf_workload, perf_baseline):
    """Time DirectNaiveProtocol._estimate_from_bitstrings (inner hot loop)."""
    from quartumse.protocols import DirectNaiveProtocol

    proto = DirectNaiveProtocol()
    # Generate representative bitstrings
    rng = np.random.default_rng(99)
    bitstrings = ["".join(str(b) for b in row) for row in rng.integers(0, 2, size=(N_SHOTS, 4))]

    def run():
        proto._estimate_from_bitstrings(bitstrings, "ZIZI", 1.0)

    times = run_timed(run, n_runs=21)
    assert_no_regression("eigenvalue_direct_naive", times, perf_baseline)


@pytest.mark.perf
def test_eigenvalue_direct_grouped(perf_workload, perf_baseline):
    """Time DirectGroupedProtocol._estimate_from_bitstrings (inner hot loop)."""
    from quartumse.protocols import DirectGroupedProtocol

    proto = DirectGroupedProtocol()
    rng = np.random.default_rng(99)
    bitstrings = ["".join(str(b) for b in row) for row in rng.integers(0, 2, size=(N_SHOTS, 4))]

    def run():
        proto._estimate_from_bitstrings(bitstrings, "ZIZI", "ZZZZ", 1.0)

    times = run_timed(run, n_runs=21)
    assert_no_regression("eigenvalue_direct_grouped", times, perf_baseline)
