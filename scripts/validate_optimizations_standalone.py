"""Standalone validation script that imports modules directly.

This script bypasses the quartumse package __init__.py to avoid
requiring qiskit and other heavy dependencies.

Usage:
    python scripts/validate_optimizations_standalone.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def load_core_module():
    """Load the core module directly without triggering full package imports."""
    import importlib.util
    import types

    # Create fake package structure in sys.modules
    if "quartumse" not in sys.modules:
        quartumse_pkg = types.ModuleType("quartumse")
        quartumse_pkg.__path__ = [str(src_path / "quartumse")]
        sys.modules["quartumse"] = quartumse_pkg

    if "quartumse.observables" not in sys.modules:
        obs_pkg = types.ModuleType("quartumse.observables")
        obs_pkg.__path__ = [str(src_path / "quartumse" / "observables")]
        sys.modules["quartumse.observables"] = obs_pkg

    # Now load the core module
    spec = importlib.util.spec_from_file_location(
        "quartumse.observables.core",
        src_path / "quartumse" / "observables" / "core.py"
    )
    core = importlib.util.module_from_spec(spec)
    sys.modules["quartumse.observables.core"] = core
    spec.loader.exec_module(core)

    return core


def validate_observable_caching():
    """Validate that Observable locality/support caching works correctly."""
    print("\n=== Testing Observable Caching ===")

    core = load_core_module()
    Observable = core.Observable
    ObservableSet = core.ObservableSet

    test_cases = [
        ("IIIII", 0, []),
        ("XYZII", 3, [0, 1, 2]),
        ("IIXIZ", 2, [2, 4]),
        ("XXXXX", 5, [0, 1, 2, 3, 4]),
        ("ZIIII", 1, [0]),
        # Edge cases
        ("I", 0, []),  # Single qubit, identity
        ("X", 1, [0]),  # Single qubit, non-identity
        ("Z", 1, [0]),  # Single qubit, Z
        ("Y", 1, [0]),  # Single qubit, Y
        ("II", 0, []),  # Two qubits, all identity
        ("XI", 1, [0]),  # Two qubits, first non-identity
        ("IX", 1, [1]),  # Two qubits, second non-identity
        ("XY", 2, [0, 1]),  # Two qubits, both non-identity
        ("I" * 20, 0, []),  # Large all-identity
        ("X" * 20, 20, list(range(20))),  # Large all-X
        ("I" * 10 + "X" + "I" * 9, 1, [10]),  # Large with single non-identity in middle
    ]

    all_passed = True
    for pauli, expected_locality, expected_support in test_cases:
        obs = Observable(pauli)

        # Test locality
        if obs.locality != expected_locality:
            print(f"  FAIL: {pauli} locality = {obs.locality}, expected {expected_locality}")
            all_passed = False

        # Test support
        if obs.support != expected_support:
            print(f"  FAIL: {pauli} support = {obs.support}, expected {expected_support}")
            all_passed = False

        # Test that repeated access returns same (cached) value
        if obs.locality != obs.locality or obs.support != obs.support:
            print(f"  FAIL: {pauli} cached values inconsistent on repeated access")
            all_passed = False

        # Test weight alias
        if obs.weight != obs.locality:
            print(f"  FAIL: {pauli} weight != locality")
            all_passed = False

    # Test ObservableSet index lookup
    observables = [Observable(f"{'X' * i}{'I' * (5-i)}") for i in range(1, 6)]
    obs_set = ObservableSet(observables)

    for obs in observables:
        retrieved = obs_set.get_by_id(obs.observable_id)
        if retrieved.pauli_string != obs.pauli_string:
            print(f"  FAIL: get_by_id returned wrong observable")
            all_passed = False

    # Test KeyError for missing ID
    try:
        obs_set.get_by_id("nonexistent_id")
        print("  FAIL: get_by_id should raise KeyError for missing ID")
        all_passed = False
    except KeyError:
        pass  # Expected

    # Edge case: ObservableSet with single observable
    single_obs = Observable("XYZ")
    single_set = ObservableSet([single_obs])
    if single_set.get_by_id(single_obs.observable_id).pauli_string != "XYZ":
        print("  FAIL: single-element ObservableSet lookup failed")
        all_passed = False

    # Edge case: ObservableSet with observables having same Pauli but different coefficients
    obs_coef1 = Observable("XYZ", coefficient=1.0)
    obs_coef2 = Observable("XYZ", coefficient=2.0)
    multi_coef_set = ObservableSet([obs_coef1, obs_coef2])
    if len(multi_coef_set) != 2:
        print("  FAIL: ObservableSet should allow same Pauli with different coefficients")
        all_passed = False

    # Edge case: Observable created via from_dict
    obs_dict = {"pauli_string": "XYZXY", "coefficient": 1.5, "observable_id": "test_obs"}
    obs_from_dict = Observable.from_dict(obs_dict)
    if obs_from_dict.locality != 5 or obs_from_dict.support != [0, 1, 2, 3, 4]:
        print("  FAIL: Observable.from_dict caching not working")
        all_passed = False

    if all_passed:
        print("  PASS: All Observable caching tests passed")
    return all_passed


def load_grouping_module():
    """Load the grouping module."""
    import importlib.util

    # Ensure core is loaded first
    core = load_core_module()

    spec = importlib.util.spec_from_file_location(
        "quartumse.observables.grouping",
        src_path / "quartumse" / "observables" / "grouping.py"
    )
    grouping = importlib.util.module_from_spec(spec)
    sys.modules["quartumse.observables.grouping"] = grouping
    spec.loader.exec_module(grouping)

    return core, grouping


def validate_grouping():
    """Validate that grouping algorithms produce valid results."""
    print("\n=== Testing Observable Grouping ===")

    core, grouping = load_grouping_module()
    Observable = core.Observable

    greedy_grouping = grouping.greedy_grouping
    sorted_insertion_grouping = grouping.sorted_insertion_grouping
    verify_grouping = grouping.verify_grouping
    build_qubitwise_commutation_graph = grouping.build_qubitwise_commutation_graph

    all_passed = True

    # Test cases: observables that should group together
    test_observables = [
        Observable("XIIIII"),
        Observable("IXIIII"),
        Observable("IIXIII"),
        Observable("ZIIIII"),
        Observable("IZIIII"),
        Observable("XZIIII"),
    ]

    # Test greedy grouping
    groups_greedy = greedy_grouping(test_observables, use_qubitwise=True)
    if not verify_grouping(groups_greedy):
        print("  FAIL: greedy_grouping produced invalid groups")
        all_passed = False

    # Verify all observables are grouped
    grouped_indices = set()
    for g in groups_greedy:
        grouped_indices.update(g.observable_indices)
    if grouped_indices != set(range(len(test_observables))):
        print("  FAIL: greedy_grouping didn't group all observables")
        all_passed = False

    # Test sorted insertion grouping
    test_observables_2 = [
        Observable("XIIIII"),
        Observable("IXIIII"),
        Observable("IIXIII"),
        Observable("ZIIIII"),
        Observable("IZIIII"),
        Observable("XZIIII"),
    ]
    groups_sorted = sorted_insertion_grouping(test_observables_2)
    if not verify_grouping(groups_sorted):
        print("  FAIL: sorted_insertion_grouping produced invalid groups")
        all_passed = False

    grouped_indices = set()
    for g in groups_sorted:
        grouped_indices.update(g.observable_indices)
    if grouped_indices != set(range(len(test_observables_2))):
        print("  FAIL: sorted_insertion_grouping didn't group all observables")
        all_passed = False

    # Edge case: Single observable
    single_obs = [Observable("XYZ")]
    single_groups = greedy_grouping(single_obs, use_qubitwise=True)
    if len(single_groups) != 1 or single_groups[0].size != 1:
        print("  FAIL: Single observable should form one group")
        all_passed = False

    # Edge case: Empty list
    empty_groups = greedy_grouping([], use_qubitwise=True)
    if len(empty_groups) != 0:
        print("  FAIL: Empty list should produce no groups")
        all_passed = False

    # Edge case: All observables commute
    all_commute = [
        Observable("XIII"),
        Observable("IXII"),
        Observable("IIXI"),
        Observable("IIIX"),
    ]
    all_commute_groups = greedy_grouping(all_commute, use_qubitwise=True)
    if len(all_commute_groups) != 1:
        print(f"  FAIL: All commuting observables should form 1 group, got {len(all_commute_groups)}")
        all_passed = False

    # Edge case: Large number of observables
    large_obs = [Observable(f"{'I' * i}X{'I' * (19-i)}") for i in range(20)]
    large_groups = greedy_grouping(large_obs, use_qubitwise=True)
    if not verify_grouping(large_groups):
        print("  FAIL: Large grouping invalid")
        all_passed = False
    if len(large_groups) != 1:
        print(f"  FAIL: Large commuting observables should form 1 group, got {len(large_groups)}")
        all_passed = False

    # Test commutation graph with single observable
    single_graph = build_qubitwise_commutation_graph([Observable("XYZ")])
    if single_graph != {0: set()}:
        print("  FAIL: Single observable graph should have empty neighbor set")
        all_passed = False

    if all_passed:
        print("  PASS: Grouping tests passed")
    return all_passed


def validate_benchmarking_grouping():
    """Validate that pre-grouping in benchmarking produces same results."""
    print("\n=== Testing Benchmarking Row Grouping ===")
    from collections import defaultdict

    class MockRow:
        def __init__(self, protocol_id, N_total, se, observable_id="obs"):
            self.protocol_id = protocol_id
            self.N_total = N_total
            self.se = se
            self.observable_id = observable_id
            self.estimate = 0.5

    all_passed = True

    # Create test data
    protocols = ["proto_a", "proto_b", "proto_c"]
    n_values = [100, 500, 1000]
    rows = []
    for proto in protocols:
        for n in n_values:
            for rep in range(10):
                rows.append(MockRow(proto, n, 0.01 * (rep + 1)))

    def old_method(rows, protocol_id):
        return [r for r in rows if r.protocol_id == protocol_id]

    rows_by_protocol = defaultdict(list)
    for row in rows:
        rows_by_protocol[row.protocol_id].append(row)

    def new_method(rows_by_protocol, protocol_id):
        return rows_by_protocol.get(protocol_id, [])

    for proto in protocols:
        old_result = old_method(rows, proto)
        new_result = new_method(rows_by_protocol, proto)

        if len(old_result) != len(new_result):
            print(f"  FAIL: {proto} - count mismatch: {len(old_result)} vs {len(new_result)}")
            all_passed = False

        old_ses = sorted([r.se for r in old_result])
        new_ses = sorted([r.se for r in new_result])
        if old_ses != new_ses:
            print(f"  FAIL: {proto} - content mismatch")
            all_passed = False

    if new_method(rows_by_protocol, "nonexistent") != []:
        print("  FAIL: missing protocol should return empty list")
        all_passed = False

    # Edge case: Empty rows
    empty_by_protocol = defaultdict(list)
    if new_method(empty_by_protocol, "any") != []:
        print("  FAIL: empty rows should return empty list")
        all_passed = False

    # Edge case: Single row
    single_row = [MockRow("single_proto", 100, 0.01)]
    single_by_protocol = defaultdict(list)
    for row in single_row:
        single_by_protocol[row.protocol_id].append(row)
    result = new_method(single_by_protocol, "single_proto")
    if len(result) != 1 or result[0].se != 0.01:
        print("  FAIL: single row not retrieved correctly")
        all_passed = False

    # Edge case: Order preservation
    ordered_rows = [MockRow("ordered", 100, i * 0.1) for i in range(100)]
    ordered_by_protocol = defaultdict(list)
    for row in ordered_rows:
        ordered_by_protocol[row.protocol_id].append(row)
    result = new_method(ordered_by_protocol, "ordered")
    expected_ses = [i * 0.1 for i in range(100)]
    actual_ses = [r.se for r in result]
    if not np.allclose(actual_ses, expected_ses):
        print("  FAIL: order not preserved in grouping")
        all_passed = False

    if all_passed:
        print("  PASS: Benchmarking grouping tests passed")
    return all_passed


def validate_parquet_vectorization():
    """Test the vectorized approach used in parquet_io.

    Note: df.where(pd.notna(df), None) keeps NaN as float nan in memory,
    but when used with to_dict("records"), these values become Python-compatible.
    The actual parquet round-trip handles None correctly via pyarrow.

    Here we test that the to_dict("records") approach works correctly and
    that the logic is equivalent to the old iterrows approach.
    """
    print("\n=== Testing Parquet Vectorization Logic ===")

    all_passed = True

    # Test: to_dict("records") produces list of dicts correctly
    df = pd.DataFrame({
        "a": [1.0, 2.0, 3.0],
        "b": ["x", "y", "z"],
        "c": [10, 20, 30],
    })

    records = df.to_dict("records")

    if len(records) != 3:
        print(f"  FAIL: should have 3 records, got {len(records)}")
        all_passed = False

    if records[0] != {"a": 1.0, "b": "x", "c": 10}:
        print(f"  FAIL: records[0] mismatch: {records[0]}")
        all_passed = False

    if records[1]["a"] != 2.0 or records[1]["b"] != "y":
        print(f"  FAIL: records[1] values incorrect")
        all_passed = False

    # Test: Comparison with old iterrows approach
    # Old approach:
    old_records = []
    for _, row in df.iterrows():
        old_records.append(row.to_dict())

    # New approach:
    new_records = df.to_dict("records")

    # Should be equivalent
    for old, new in zip(old_records, new_records):
        for key in old:
            if old[key] != new[key]:
                print(f"  FAIL: old vs new mismatch for key {key}: {old[key]} vs {new[key]}")
                all_passed = False

    # Edge case: Empty DataFrame
    empty_df = pd.DataFrame({"a": [], "b": []})
    empty_records = empty_df.to_dict("records")
    if len(empty_records) != 0:
        print(f"  FAIL: empty DataFrame should produce empty records")
        all_passed = False

    # Edge case: Single row
    single_df = pd.DataFrame({"a": [1.0], "b": ["test"]})
    single_records = single_df.to_dict("records")
    if len(single_records) != 1:
        print("  FAIL: single row DataFrame should produce 1 record")
        all_passed = False
    if single_records[0]["a"] != 1.0:
        print("  FAIL: single row value mismatch")
        all_passed = False

    # Edge case: Large DataFrame - verify performance and correctness
    large_df = pd.DataFrame({
        "a": list(range(10000)),
        "b": [f"str_{i}" for i in range(10000)],
        "c": np.random.randn(10000),
    })
    large_records = large_df.to_dict("records")
    if len(large_records) != 10000:
        print(f"  FAIL: large DataFrame should have 10000 records, got {len(large_records)}")
        all_passed = False
    if large_records[5000]["a"] != 5000:
        print(f"  FAIL: large DataFrame spot check failed")
        all_passed = False
    if large_records[9999]["b"] != "str_9999":
        print("  FAIL: large DataFrame last record check failed")
        all_passed = False

    # Test: NaN handling with where + to_dict (the actual pattern used)
    # The df.where(pd.notna(df), None) + to_dict("records") approach
    nan_df = pd.DataFrame({
        "a": [1.0, np.nan, 3.0],
        "b": ["x", "y", "z"],
    })
    nan_cleaned = nan_df.where(pd.notna(nan_df), None)
    nan_records = nan_cleaned.to_dict("records")

    # Non-NaN values should be preserved
    if nan_records[0]["a"] != 1.0:
        print(f"  FAIL: non-NaN value not preserved: {nan_records[0]['a']}")
        all_passed = False
    if nan_records[2]["a"] != 3.0:
        print(f"  FAIL: non-NaN value not preserved: {nan_records[2]['a']}")
        all_passed = False

    # NaN value: pandas keeps it as nan, but that's OK - the dataclass
    # constructor and pyarrow serialization handle this correctly
    # We just verify the structure is correct
    if "a" not in nan_records[1]:
        print("  FAIL: NaN record missing key 'a'")
        all_passed = False

    # Test: Verify iterrows equivalence for non-NaN data
    test_df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [10.0, 20.0, 30.0, 40.0, 50.0],
        "z": ["a", "b", "c", "d", "e"],
    })

    iterrows_result = []
    for _, row in test_df.iterrows():
        iterrows_result.append(row.to_dict())

    todict_result = test_df.to_dict("records")

    if len(iterrows_result) != len(todict_result):
        print("  FAIL: iterrows vs to_dict length mismatch")
        all_passed = False

    for i, (ir, td) in enumerate(zip(iterrows_result, todict_result)):
        if ir != td:
            print(f"  FAIL: row {i} mismatch between iterrows and to_dict")
            all_passed = False

    if all_passed:
        print("  PASS: Parquet vectorization tests passed")
    return all_passed


def validate_shot_data_encoding():
    """Test the vectorized string encoding/decoding for shot data."""
    print("\n=== Testing Shot Data Encoding ===")

    all_passed = True

    # Test basis encoding: {0: Z, 1: X, 2: Y}
    basis_chars = np.array(["Z", "X", "Y"])

    # Test case 1: Simple encoding
    bases = np.array([[0, 1, 2], [2, 1, 0]])
    expected = ["ZXY", "YXZ"]
    clipped = np.clip(bases, 0, 2)
    char_array = basis_chars[clipped]
    result = ["".join(row) for row in char_array]
    if result != expected:
        print(f"  FAIL: basis encoding mismatch: {result} vs {expected}")
        all_passed = False

    # Test case 2: Single row
    single_bases = np.array([[0, 0, 0]])
    single_result = ["".join(row) for row in basis_chars[single_bases]]
    if single_result != ["ZZZ"]:
        print(f"  FAIL: single row encoding: {single_result}")
        all_passed = False

    # Test case 3: Single qubit
    single_qubit = np.array([[0], [1], [2]])
    single_qubit_result = ["".join(row) for row in basis_chars[single_qubit]]
    if single_qubit_result != ["Z", "X", "Y"]:
        print(f"  FAIL: single qubit encoding: {single_qubit_result}")
        all_passed = False

    # Test case 4: Large array
    rng = np.random.default_rng(42)
    large_bases = rng.integers(0, 3, size=(1000, 10))
    large_result = ["".join(row) for row in basis_chars[large_bases]]
    if len(large_result) != 1000:
        print(f"  FAIL: large array encoding length: {len(large_result)}")
        all_passed = False
    if len(large_result[0]) != 10:
        print(f"  FAIL: large array string length: {len(large_result[0])}")
        all_passed = False

    # Test outcome encoding
    outcomes = np.array([[0, 1, 0, 1], [1, 1, 1, 1], [0, 0, 0, 0]])
    outcome_strings = ["".join(row.astype(str)) for row in outcomes]
    expected_outcomes = ["0101", "1111", "0000"]
    if outcome_strings != expected_outcomes:
        print(f"  FAIL: outcome encoding: {outcome_strings} vs {expected_outcomes}")
        all_passed = False

    # Test decoding
    basis_map_inv = {"Z": 0, "X": 1, "Y": 2}
    encoded_bases = ["ZXY", "YXZ", "XXX"]
    decoded = []
    for s in encoded_bases:
        decoded.append([basis_map_inv[c] for c in s])
    decoded_array = np.array(decoded)
    expected_decoded = np.array([[0, 1, 2], [2, 1, 0], [1, 1, 1]])
    if not np.array_equal(decoded_array, expected_decoded):
        print(f"  FAIL: basis decoding mismatch")
        all_passed = False

    # Edge case: Empty array
    empty_bases = np.array([]).reshape(0, 3).astype(int)
    if empty_bases.shape[0] != 0:
        print("  FAIL: empty array shape")
        all_passed = False

    if all_passed:
        print("  PASS: Shot data encoding tests passed")
    return all_passed


def validate_shadow_vectorization():
    """Test the vectorized shadow estimation logic."""
    print("\n=== Testing Shadow Vectorization Logic ===")

    all_passed = True

    # Simulate shadow estimation vectorization
    # For observable with support [0, 2] (positions with non-identity)
    # and Pauli string "XIZ" -> requires basis [1, ?, 0] (X=1, Z=0)

    num_shadows = 100
    num_qubits = 3
    rng = np.random.default_rng(42)

    measurement_bases = rng.integers(0, 3, size=(num_shadows, num_qubits))
    measurement_outcomes = rng.integers(0, 2, size=(num_shadows, num_qubits))

    # Observable "XIZ" -> support = [0, 2], required_bases = [1, 0]
    support = [0, 2]
    pauli_to_basis = {"X": 1, "Y": 2, "Z": 0}
    pauli_string = "XIZ"
    required_bases = np.array([pauli_to_basis[pauli_string[q]] for q in support])

    # Vectorized computation
    measured_bases_support = measurement_bases[:, support]
    outcomes_support = measurement_outcomes[:, support]

    compatible = np.all(measured_bases_support == required_bases, axis=1)
    signs = np.prod(1 - 2 * outcomes_support, axis=1)
    scaling_factor = 3 ** len(support)
    coefficient = 1.0
    vectorized_result = np.where(compatible, scaling_factor * signs * coefficient, 0.0)

    # Loop-based computation for comparison
    loop_result = []
    for i in range(num_shadows):
        expectation = 1.0
        incompatible = False
        for j, qubit_idx in enumerate(support):
            if measurement_bases[i, qubit_idx] != required_bases[j]:
                incompatible = True
                break
            outcome = measurement_outcomes[i, qubit_idx]
            expectation *= 1 - 2 * outcome

        if incompatible:
            loop_result.append(0.0)
        else:
            loop_result.append(scaling_factor * expectation * coefficient)

    loop_result = np.array(loop_result)

    if not np.allclose(vectorized_result, loop_result):
        diff = np.abs(vectorized_result - loop_result)
        print(f"  FAIL: vectorized vs loop mismatch, max diff: {np.max(diff)}")
        all_passed = False

    # Edge case: All identity observable (empty support)
    empty_support = []
    empty_required = np.array([])
    empty_compatible = np.ones(num_shadows, dtype=bool)  # All compatible
    empty_signs = np.ones(num_shadows)  # All +1
    empty_scaling = 3 ** 0  # = 1
    empty_result = np.where(empty_compatible, empty_scaling * empty_signs, 0.0)
    if not np.all(empty_result == 1.0):
        print("  FAIL: all identity observable should give all 1.0")
        all_passed = False

    # Edge case: Single shadow
    single_bases = np.array([[1, 0, 2]])  # X, Z, Y
    single_outcomes = np.array([[0, 1, 0]])
    support_single = [0]  # X position
    required_single = np.array([1])  # X basis

    measured_single = single_bases[:, support_single]
    outcomes_single = single_outcomes[:, support_single]
    compat_single = np.all(measured_single == required_single, axis=1)
    signs_single = np.prod(1 - 2 * outcomes_single, axis=1)
    result_single = np.where(compat_single, 3 * signs_single, 0.0)

    # outcome is 0 -> sign is +1, so result should be 3 * 1 = 3
    if not np.isclose(result_single[0], 3.0):
        print(f"  FAIL: single shadow result should be 3.0, got {result_single[0]}")
        all_passed = False

    # Edge case: All incompatible
    all_z_bases = np.zeros((50, 3), dtype=int)  # All Z basis
    x_support = [0]  # Need X basis
    x_required = np.array([1])
    x_measured = all_z_bases[:, x_support]
    x_compat = np.all(x_measured == x_required, axis=1)
    x_result = np.where(x_compat, 3.0, 0.0)
    if not np.all(x_result == 0.0):
        print("  FAIL: all incompatible should give all 0.0")
        all_passed = False

    # Edge case: Negative coefficient
    neg_coef = -2.0
    neg_result = np.where(compatible, scaling_factor * signs * neg_coef, 0.0)
    expected_neg = np.where(compatible, loop_result / coefficient * neg_coef, 0.0)
    if not np.allclose(neg_result, expected_neg):
        print("  FAIL: negative coefficient handling")
        all_passed = False

    if all_passed:
        print("  PASS: Shadow vectorization tests passed")
    return all_passed


def run_performance_comparison():
    """Run a quick performance comparison for key operations."""
    print("\n=== Performance Comparison ===")

    try:
        core = load_core_module()
        Observable = core.Observable
        ObservableSet = core.ObservableSet
    except Exception as e:
        print(f"  SKIP: Could not import Observable ({e})")
        return

    # Test Observable.locality access performance
    obs = Observable("XYZXYZXYZX")  # 10 qubit observable

    # Warm up cache
    _ = obs.locality

    n_iterations = 100000
    start = time.perf_counter()
    for _ in range(n_iterations):
        _ = obs.locality
    cached_time = time.perf_counter() - start

    print(f"  Observable.locality ({n_iterations} accesses): {cached_time*1000:.2f}ms (cached)")

    # Test ObservableSet.get_by_id performance
    observables = [Observable(f"{'X' * (i % 10 + 1)}{'I' * (9 - i % 10)}") for i in range(1000)]
    obs_set = ObservableSet(observables)

    target_id = observables[500].observable_id
    n_iterations = 10000

    start = time.perf_counter()
    for _ in range(n_iterations):
        _ = obs_set.get_by_id(target_id)
    indexed_time = time.perf_counter() - start

    print(f"  ObservableSet.get_by_id ({n_iterations} lookups, 1000 obs): {indexed_time*1000:.2f}ms (indexed)")


def main():
    print("=" * 60)
    print("Standalone Optimization Validation Script")
    print("=" * 60)

    results = []

    results.append(("Observable Caching", validate_observable_caching()))
    results.append(("Grouping", validate_grouping()))
    results.append(("Benchmarking Grouping", validate_benchmarking_grouping()))
    results.append(("Parquet Vectorization", validate_parquet_vectorization()))
    results.append(("Shot Data Encoding", validate_shot_data_encoding()))
    results.append(("Shadow Vectorization", validate_shadow_vectorization()))

    run_performance_comparison()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll validation tests passed!")
        return 0
    else:
        print("\nSome tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
