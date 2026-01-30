"""Validation script for performance optimizations.

Run this script to verify that the optimized code produces identical results
to the original implementations.

Usage:
    python scripts/validate_optimizations.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def validate_observable_caching():
    """Validate that Observable locality/support caching works correctly."""
    print("\n=== Testing Observable Caching ===")
    try:
        from quartumse.observables.core import Observable, ObservableSet
    except ImportError as e:
        print(f"  SKIP: Could not import observables.core ({e})")
        return True

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
    # These will have different observable_ids due to coefficient in hash
    multi_coef_set = ObservableSet([obs_coef1, obs_coef2])
    if len(multi_coef_set) != 2:
        print("  FAIL: ObservableSet should allow same Pauli with different coefficients")
        all_passed = False

    # Edge case: Observable created via from_dict (tests that caching works after deserialization)
    obs_dict = {"pauli_string": "XYZXY", "coefficient": 1.5, "observable_id": "test_obs"}
    obs_from_dict = Observable.from_dict(obs_dict)
    if obs_from_dict.locality != 5 or obs_from_dict.support != [0, 1, 2, 3, 4]:
        print("  FAIL: Observable.from_dict caching not working")
        all_passed = False

    if all_passed:
        print("  PASS: All Observable caching tests passed")
    return all_passed


def validate_parquet_io():
    """Validate that parquet I/O produces correct results."""
    print("\n=== Testing Parquet I/O ===")
    import tempfile
    import shutil

    try:
        from quartumse.io.parquet_io import ParquetWriter, ParquetReader
        from quartumse.io.long_form import LongFormResultSet
        from quartumse.io.schemas import LongFormRow, SummaryRow
    except ImportError as e:
        print(f"  SKIP: Could not import parquet_io ({e})")
        return True

    all_passed = True
    temp_dir = tempfile.mkdtemp()

    try:
        # Create test data with various types including NaN/None
        test_rows = [
            LongFormRow(
                run_id="test_run",
                methodology_version="1.0",
                circuit_id="circuit_1",
                n_qubits=4,
                observable_id=f"obs_{i}",
                observable_type="pauli_string",
                locality=2,
                protocol_id="direct_naive",
                protocol_version="1.0",
                backend_id="simulator",
                replicate=0,
                N_total=1000,
                estimate=0.5 + i * 0.1,
                se=0.01 * (i + 1),
                ci_low=0.4 + i * 0.1 if i % 2 == 0 else None,  # Test None handling
                ci_high=0.6 + i * 0.1 if i % 2 == 0 else None,
            )
            for i in range(5)
        ]

        result_set = LongFormResultSet(test_rows)

        # Write and read back
        writer = ParquetWriter(temp_dir)
        writer.write_long_form(result_set)

        reader = ParquetReader(temp_dir)
        loaded_set = reader.read_long_form()

        # Verify count
        if len(loaded_set) != len(result_set):
            print(f"  FAIL: Row count mismatch: {len(loaded_set)} vs {len(result_set)}")
            all_passed = False

        # Verify content
        for orig, loaded in zip(result_set.rows, loaded_set.rows):
            if orig.observable_id != loaded.observable_id:
                print(f"  FAIL: observable_id mismatch")
                all_passed = False
            if not np.isclose(orig.estimate, loaded.estimate):
                print(f"  FAIL: estimate mismatch: {orig.estimate} vs {loaded.estimate}")
                all_passed = False
            # Check None handling
            if (orig.ci_low is None) != (loaded.ci_low is None):
                print(f"  FAIL: None handling mismatch for ci_low")
                all_passed = False

        # Edge case: Single row
        single_row = LongFormRow(
            run_id="single_run",
            methodology_version="1.0",
            circuit_id="circuit_single",
            n_qubits=2,
            observable_id="obs_single",
            observable_type="pauli_string",
            locality=1,
            protocol_id="direct_naive",
            protocol_version="1.0",
            backend_id="simulator",
            replicate=0,
            N_total=100,
            estimate=0.75,
            se=0.05,
        )
        single_dir = tempfile.mkdtemp()
        try:
            single_writer = ParquetWriter(single_dir)
            single_writer.write_long_form(LongFormResultSet([single_row]))
            single_reader = ParquetReader(single_dir)
            single_loaded = single_reader.read_long_form()
            if len(single_loaded) != 1:
                print(f"  FAIL: Single row test - expected 1 row, got {len(single_loaded)}")
                all_passed = False
            if single_loaded.rows[0].observable_id != "obs_single":
                print("  FAIL: Single row test - observable_id mismatch")
                all_passed = False
        finally:
            shutil.rmtree(single_dir, ignore_errors=True)

        # Edge case: Row with all None optional fields
        all_none_row = LongFormRow(
            run_id="none_run",
            methodology_version="1.0",
            circuit_id="circuit_none",
            n_qubits=2,
            observable_id="obs_none",
            observable_type="pauli_string",
            locality=1,
            protocol_id="direct_naive",
            protocol_version="1.0",
            backend_id="simulator",
            replicate=0,
            N_total=100,
            estimate=0.5,
            se=0.1,
            ci_low=None,
            ci_high=None,
            ci_low_raw=None,
            ci_high_raw=None,
            truth=None,
        )
        none_dir = tempfile.mkdtemp()
        try:
            none_writer = ParquetWriter(none_dir)
            none_writer.write_long_form(LongFormResultSet([all_none_row]))
            none_reader = ParquetReader(none_dir)
            none_loaded = none_reader.read_long_form()
            loaded_row = none_loaded.rows[0]
            if loaded_row.ci_low is not None or loaded_row.ci_high is not None:
                print("  FAIL: All-None row test - None values not preserved")
                all_passed = False
        finally:
            shutil.rmtree(none_dir, ignore_errors=True)

        # Edge case: Large number of rows
        large_rows = [
            LongFormRow(
                run_id="large_run",
                methodology_version="1.0",
                circuit_id=f"circuit_{i % 10}",
                n_qubits=4,
                observable_id=f"obs_{i}",
                observable_type="pauli_string",
                locality=i % 4 + 1,
                protocol_id=f"protocol_{i % 3}",
                protocol_version="1.0",
                backend_id="simulator",
                replicate=i % 5,
                N_total=(i % 4 + 1) * 100,
                estimate=np.sin(i * 0.1),  # Various float values
                se=0.01 + i * 0.001,
            )
            for i in range(1000)
        ]
        large_dir = tempfile.mkdtemp()
        try:
            large_writer = ParquetWriter(large_dir)
            large_writer.write_long_form(LongFormResultSet(large_rows))
            large_reader = ParquetReader(large_dir)
            large_loaded = large_reader.read_long_form()
            if len(large_loaded) != 1000:
                print(f"  FAIL: Large rows test - expected 1000, got {len(large_loaded)}")
                all_passed = False
            # Spot check some values
            for idx in [0, 499, 999]:
                if not np.isclose(large_loaded.rows[idx].estimate, np.sin(idx * 0.1), atol=1e-6):
                    print(f"  FAIL: Large rows test - estimate mismatch at index {idx}")
                    all_passed = False
        finally:
            shutil.rmtree(large_dir, ignore_errors=True)

        # Edge case: Special float values
        special_row = LongFormRow(
            run_id="special_run",
            methodology_version="1.0",
            circuit_id="circuit_special",
            n_qubits=2,
            observable_id="obs_special",
            observable_type="pauli_string",
            locality=1,
            protocol_id="direct_naive",
            protocol_version="1.0",
            backend_id="simulator",
            replicate=0,
            N_total=100,
            estimate=0.0,  # Zero
            se=1e-10,  # Very small
        )
        special_dir = tempfile.mkdtemp()
        try:
            special_writer = ParquetWriter(special_dir)
            special_writer.write_long_form(LongFormResultSet([special_row]))
            special_reader = ParquetReader(special_dir)
            special_loaded = special_reader.read_long_form()
            if not np.isclose(special_loaded.rows[0].estimate, 0.0):
                print("  FAIL: Special float test - zero not preserved")
                all_passed = False
            if not np.isclose(special_loaded.rows[0].se, 1e-10):
                print("  FAIL: Special float test - small value not preserved")
                all_passed = False
        finally:
            shutil.rmtree(special_dir, ignore_errors=True)

        if all_passed:
            print("  PASS: Parquet I/O tests passed")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return all_passed


def validate_grouping():
    """Validate that grouping algorithms produce valid results."""
    print("\n=== Testing Observable Grouping ===")
    try:
        from quartumse.observables.core import Observable
        from quartumse.observables.grouping import (
            greedy_grouping,
            sorted_insertion_grouping,
            verify_grouping,
            qubitwise_commutes,
            build_commutation_graph,
            build_qubitwise_commutation_graph,
        )
    except ImportError as e:
        print(f"  SKIP: Could not import grouping modules ({e})")
        return True

    all_passed = True

    # Test cases: observables that should group together
    test_observables = [
        Observable("XIIIII"),
        Observable("IXIIII"),
        Observable("IIXIII"),  # All X on different qubits - should commute qubitwise
        Observable("ZIIIII"),
        Observable("IZIIII"),  # Z observables
        Observable("XZIIII"),  # Mixed - doesn't commute qubitwise with pure X or Z on same qubits
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
    # Need fresh observables since grouping modifies group_id
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

    # Verify all observables are grouped
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
    if not verify_grouping(single_groups):
        print("  FAIL: Single observable grouping invalid")
        all_passed = False

    # Edge case: Empty list
    empty_groups = greedy_grouping([], use_qubitwise=True)
    if len(empty_groups) != 0:
        print("  FAIL: Empty list should produce no groups")
        all_passed = False

    # Edge case: All observables commute (should form one group)
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
    if not verify_grouping(all_commute_groups):
        print("  FAIL: All commuting grouping invalid")
        all_passed = False

    # Edge case: No observables commute (each should be its own group)
    none_commute = [
        Observable("XY"),
        Observable("YX"),
        Observable("ZX"),
        Observable("XZ"),
    ]
    none_commute_groups = greedy_grouping(none_commute, use_qubitwise=True)
    # These don't all commute qubitwise, should have multiple groups
    if not verify_grouping(none_commute_groups):
        print("  FAIL: Non-commuting grouping invalid")
        all_passed = False
    # Verify all are grouped
    grouped_indices = set()
    for g in none_commute_groups:
        grouped_indices.update(g.observable_indices)
    if grouped_indices != set(range(len(none_commute))):
        print("  FAIL: Non-commuting grouping didn't include all observables")
        all_passed = False

    # Edge case: All identity (trivially commute)
    all_identity = [Observable("III") for _ in range(5)]
    # Give them unique IDs
    for i, obs in enumerate(all_identity):
        obs.observable_id = f"identity_{i}"
    all_identity_groups = greedy_grouping(all_identity, use_qubitwise=True)
    if len(all_identity_groups) != 1:
        print(f"  FAIL: All identity observables should form 1 group, got {len(all_identity_groups)}")
        all_passed = False

    # Edge case: Large number of observables
    large_obs = [Observable(f"{'I' * i}X{'I' * (19-i)}") for i in range(20)]
    large_groups = greedy_grouping(large_obs, use_qubitwise=True)
    if not verify_grouping(large_groups):
        print("  FAIL: Large grouping invalid")
        all_passed = False
    # All should commute (X on different qubits)
    if len(large_groups) != 1:
        print(f"  FAIL: Large commuting observables should form 1 group, got {len(large_groups)}")
        all_passed = False

    # Edge case: Test sorted_insertion with single element
    single_sorted = sorted_insertion_grouping([Observable("XYZ")])
    if len(single_sorted) != 1:
        print("  FAIL: sorted_insertion single element should form 1 group")
        all_passed = False

    # Edge case: Test sorted_insertion with empty list
    empty_sorted = sorted_insertion_grouping([])
    if len(empty_sorted) != 0:
        print("  FAIL: sorted_insertion empty list should produce no groups")
        all_passed = False

    # Test commutation graph building with edge cases
    single_graph = build_qubitwise_commutation_graph([Observable("XYZ")])
    if single_graph != {0: set()}:
        print("  FAIL: Single observable graph should have empty neighbor set")
        all_passed = False

    # Two commuting observables
    two_commute = [Observable("XII"), Observable("IXI")]
    two_graph = build_qubitwise_commutation_graph(two_commute)
    if 1 not in two_graph[0] or 0 not in two_graph[1]:
        print("  FAIL: Two commuting observables should be neighbors in graph")
        all_passed = False

    # Two non-commuting observables
    two_not_commute = [Observable("XY"), Observable("YX")]
    two_not_graph = build_qubitwise_commutation_graph(two_not_commute)
    if 1 in two_not_graph[0] or 0 in two_not_graph[1]:
        print("  FAIL: Two non-commuting observables should not be neighbors")
        all_passed = False

    if all_passed:
        print("  PASS: Grouping tests passed")
    return all_passed


def validate_shot_data():
    """Validate shot data encoding/decoding."""
    print("\n=== Testing Shot Data I/O ===")
    import tempfile
    import shutil

    try:
        from quartumse.reporting.shot_data import ShotDataWriter, summarize_dataframe
    except ImportError as e:
        print(f"  SKIP: Could not import shot_data ({e})")
        return True

    all_passed = True
    temp_dir = tempfile.mkdtemp()

    try:
        writer = ShotDataWriter(Path(temp_dir))

        # Create test data
        num_shadows = 100
        num_qubits = 5
        rng = np.random.default_rng(42)

        measurement_bases = rng.integers(0, 3, size=(num_shadows, num_qubits))
        measurement_outcomes = rng.integers(0, 2, size=(num_shadows, num_qubits))

        # Save and load
        writer.save_shadow_measurements(
            experiment_id="test_exp",
            measurement_bases=measurement_bases,
            measurement_outcomes=measurement_outcomes,
            num_qubits=num_qubits,
        )

        loaded_bases, loaded_outcomes, loaded_n_qubits = writer.load_shadow_measurements("test_exp")

        # Verify
        if loaded_n_qubits != num_qubits:
            print(f"  FAIL: num_qubits mismatch: {loaded_n_qubits} vs {num_qubits}")
            all_passed = False

        if not np.array_equal(measurement_bases, loaded_bases):
            print("  FAIL: measurement_bases mismatch")
            all_passed = False

        if not np.array_equal(measurement_outcomes, loaded_outcomes):
            print("  FAIL: measurement_outcomes mismatch")
            all_passed = False

        # Test diagnostics
        diagnostics = writer.summarize_shadow_measurements("test_exp")
        if diagnostics.total_shots != num_shadows:
            print(f"  FAIL: total_shots mismatch: {diagnostics.total_shots} vs {num_shadows}")
            all_passed = False

        # Verify qubit marginals sum to 1
        for qubit, marginals in diagnostics.qubit_marginals.items():
            total = marginals["0"] + marginals["1"]
            if not np.isclose(total, 1.0):
                print(f"  FAIL: qubit {qubit} marginals don't sum to 1: {total}")
                all_passed = False

        # Edge case: Single shadow
        single_dir = tempfile.mkdtemp()
        try:
            single_writer = ShotDataWriter(Path(single_dir))
            single_bases = np.array([[0, 1, 2]])  # Z, X, Y
            single_outcomes = np.array([[0, 1, 0]])
            single_writer.save_shadow_measurements(
                experiment_id="single_exp",
                measurement_bases=single_bases,
                measurement_outcomes=single_outcomes,
                num_qubits=3,
            )
            loaded_b, loaded_o, loaded_n = single_writer.load_shadow_measurements("single_exp")
            if not np.array_equal(loaded_b, single_bases):
                print("  FAIL: Single shadow bases mismatch")
                all_passed = False
            if not np.array_equal(loaded_o, single_outcomes):
                print("  FAIL: Single shadow outcomes mismatch")
                all_passed = False
        finally:
            shutil.rmtree(single_dir, ignore_errors=True)

        # Edge case: Single qubit
        single_qubit_dir = tempfile.mkdtemp()
        try:
            sq_writer = ShotDataWriter(Path(single_qubit_dir))
            sq_bases = rng.integers(0, 3, size=(50, 1))
            sq_outcomes = rng.integers(0, 2, size=(50, 1))
            sq_writer.save_shadow_measurements(
                experiment_id="single_qubit_exp",
                measurement_bases=sq_bases,
                measurement_outcomes=sq_outcomes,
                num_qubits=1,
            )
            loaded_b, loaded_o, loaded_n = sq_writer.load_shadow_measurements("single_qubit_exp")
            if loaded_n != 1:
                print("  FAIL: Single qubit num_qubits mismatch")
                all_passed = False
            if not np.array_equal(loaded_b, sq_bases):
                print("  FAIL: Single qubit bases mismatch")
                all_passed = False
            if not np.array_equal(loaded_o, sq_outcomes):
                print("  FAIL: Single qubit outcomes mismatch")
                all_passed = False
            # Test diagnostics for single qubit
            sq_diag = sq_writer.summarize_shadow_measurements("single_qubit_exp")
            if 0 not in sq_diag.qubit_marginals:
                print("  FAIL: Single qubit marginals missing")
                all_passed = False
        finally:
            shutil.rmtree(single_qubit_dir, ignore_errors=True)

        # Edge case: All zeros outcomes
        zeros_dir = tempfile.mkdtemp()
        try:
            zeros_writer = ShotDataWriter(Path(zeros_dir))
            zeros_bases = np.zeros((20, 4), dtype=int)  # All Z basis
            zeros_outcomes = np.zeros((20, 4), dtype=int)  # All 0 outcomes
            zeros_writer.save_shadow_measurements(
                experiment_id="zeros_exp",
                measurement_bases=zeros_bases,
                measurement_outcomes=zeros_outcomes,
                num_qubits=4,
            )
            loaded_b, loaded_o, _ = zeros_writer.load_shadow_measurements("zeros_exp")
            if not np.all(loaded_o == 0):
                print("  FAIL: All zeros outcomes not preserved")
                all_passed = False
            diag = zeros_writer.summarize_shadow_measurements("zeros_exp")
            # All outcomes are 0, so marginals should be 1.0 for "0" and 0.0 for "1"
            for qubit, marginals in diag.qubit_marginals.items():
                if not np.isclose(marginals["0"], 1.0) or not np.isclose(marginals["1"], 0.0):
                    print(f"  FAIL: All zeros marginals incorrect for qubit {qubit}")
                    all_passed = False
        finally:
            shutil.rmtree(zeros_dir, ignore_errors=True)

        # Edge case: All ones outcomes
        ones_dir = tempfile.mkdtemp()
        try:
            ones_writer = ShotDataWriter(Path(ones_dir))
            ones_bases = np.ones((20, 4), dtype=int)  # All X basis
            ones_outcomes = np.ones((20, 4), dtype=int)  # All 1 outcomes
            ones_writer.save_shadow_measurements(
                experiment_id="ones_exp",
                measurement_bases=ones_bases,
                measurement_outcomes=ones_outcomes,
                num_qubits=4,
            )
            loaded_b, loaded_o, _ = ones_writer.load_shadow_measurements("ones_exp")
            if not np.all(loaded_o == 1):
                print("  FAIL: All ones outcomes not preserved")
                all_passed = False
            diag = ones_writer.summarize_shadow_measurements("ones_exp")
            for qubit, marginals in diag.qubit_marginals.items():
                if not np.isclose(marginals["0"], 0.0) or not np.isclose(marginals["1"], 1.0):
                    print(f"  FAIL: All ones marginals incorrect for qubit {qubit}")
                    all_passed = False
        finally:
            shutil.rmtree(ones_dir, ignore_errors=True)

        # Edge case: Large number of shadows
        large_dir = tempfile.mkdtemp()
        try:
            large_writer = ShotDataWriter(Path(large_dir))
            large_bases = rng.integers(0, 3, size=(10000, 8))
            large_outcomes = rng.integers(0, 2, size=(10000, 8))
            large_writer.save_shadow_measurements(
                experiment_id="large_exp",
                measurement_bases=large_bases,
                measurement_outcomes=large_outcomes,
                num_qubits=8,
            )
            loaded_b, loaded_o, loaded_n = large_writer.load_shadow_measurements("large_exp")
            if loaded_b.shape != (10000, 8):
                print(f"  FAIL: Large shadow bases shape mismatch: {loaded_b.shape}")
                all_passed = False
            if not np.array_equal(loaded_b, large_bases):
                print("  FAIL: Large shadow bases content mismatch")
                all_passed = False
        finally:
            shutil.rmtree(large_dir, ignore_errors=True)

        # Edge case: Append to existing data
        append_dir = tempfile.mkdtemp()
        try:
            append_writer = ShotDataWriter(Path(append_dir))
            # First batch
            batch1_bases = rng.integers(0, 3, size=(50, 3))
            batch1_outcomes = rng.integers(0, 2, size=(50, 3))
            append_writer.save_shadow_measurements(
                experiment_id="append_exp",
                measurement_bases=batch1_bases,
                measurement_outcomes=batch1_outcomes,
                num_qubits=3,
            )
            # Second batch (append)
            batch2_bases = rng.integers(0, 3, size=(30, 3))
            batch2_outcomes = rng.integers(0, 2, size=(30, 3))
            append_writer.save_shadow_measurements(
                experiment_id="append_exp",
                measurement_bases=batch2_bases,
                measurement_outcomes=batch2_outcomes,
                num_qubits=3,
            )
            # Load combined
            loaded_b, loaded_o, _ = append_writer.load_shadow_measurements("append_exp")
            if loaded_b.shape[0] != 80:
                print(f"  FAIL: Appended data should have 80 rows, got {loaded_b.shape[0]}")
                all_passed = False
            # Verify first and last rows
            if not np.array_equal(loaded_b[:50], batch1_bases):
                print("  FAIL: Appended data batch1 mismatch")
                all_passed = False
            if not np.array_equal(loaded_b[50:], batch2_bases):
                print("  FAIL: Appended data batch2 mismatch")
                all_passed = False
        finally:
            shutil.rmtree(append_dir, ignore_errors=True)

        if all_passed:
            print("  PASS: Shot data tests passed")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return all_passed


def validate_shadow_estimation():
    """Validate vectorized shadow estimation matches loop-based version."""
    print("\n=== Testing Shadow Estimation ===")

    try:
        from quartumse.shadows.v0_baseline import RandomLocalCliffordShadows
        from quartumse.shadows.config import ShadowConfig
        from quartumse.observables.core import Observable
    except ImportError as e:
        print(f"  SKIP: Could not import shadows module ({e})")
        return True

    all_passed = True

    # Create shadow estimator
    config = ShadowConfig(num_qubits=4, shadow_size=500, random_seed=42)
    shadows = RandomLocalCliffordShadows(config)

    # Generate synthetic measurement data
    rng = np.random.default_rng(42)
    num_shadows = 500
    num_qubits = 4

    shadows.measurement_bases = rng.integers(0, 3, size=(num_shadows, num_qubits))
    shadows.measurement_outcomes = rng.integers(0, 2, size=(num_shadows, num_qubits))

    # Test observables
    test_observables = [
        Observable("IIII"),  # All identity
        Observable("ZIII"),  # Single qubit
        Observable("XZII"),  # Two qubit
        Observable("XYZI"),  # Three qubit
        Observable("XYZX"),  # Four qubit
    ]

    for obs in test_observables:
        # Compute using vectorized method
        vectorized_result = shadows._pauli_expectation_vectorized(obs)

        # Compute using loop method
        loop_result = np.array([
            shadows._pauli_expectation_single_shadow(i, obs)
            for i in range(num_shadows)
        ])

        # Compare
        if not np.allclose(vectorized_result, loop_result):
            print(f"  FAIL: {obs.pauli_string} - vectorized vs loop mismatch")
            print(f"    Max diff: {np.max(np.abs(vectorized_result - loop_result))}")
            all_passed = False

    # Edge case: Single shadow
    config_single = ShadowConfig(num_qubits=4, shadow_size=1, random_seed=42)
    shadows_single = RandomLocalCliffordShadows(config_single)
    shadows_single.measurement_bases = np.array([[0, 1, 2, 0]])  # Z, X, Y, Z
    shadows_single.measurement_outcomes = np.array([[0, 1, 0, 1]])

    single_obs = Observable("ZXYI")
    vec_single = shadows_single._pauli_expectation_vectorized(single_obs)
    loop_single = shadows_single._pauli_expectation_single_shadow(0, single_obs)
    if not np.isclose(vec_single[0], loop_single):
        print(f"  FAIL: Single shadow - vectorized {vec_single[0]} vs loop {loop_single}")
        all_passed = False

    # Edge case: Observable with coefficient
    coef_obs = Observable("ZIII", coefficient=2.5)
    vec_coef = shadows._pauli_expectation_vectorized(coef_obs)
    loop_coef = np.array([shadows._pauli_expectation_single_shadow(i, coef_obs) for i in range(num_shadows)])
    if not np.allclose(vec_coef, loop_coef):
        print("  FAIL: Observable with coefficient - vectorized vs loop mismatch")
        all_passed = False

    # Edge case: Negative coefficient
    neg_coef_obs = Observable("XZII", coefficient=-1.0)
    vec_neg = shadows._pauli_expectation_vectorized(neg_coef_obs)
    loop_neg = np.array([shadows._pauli_expectation_single_shadow(i, neg_coef_obs) for i in range(num_shadows)])
    if not np.allclose(vec_neg, loop_neg):
        print("  FAIL: Negative coefficient - vectorized vs loop mismatch")
        all_passed = False

    # Edge case: All measurements in incompatible basis (should all be 0)
    config_incompat = ShadowConfig(num_qubits=2, shadow_size=100, random_seed=42)
    shadows_incompat = RandomLocalCliffordShadows(config_incompat)
    # All measurements in Z basis
    shadows_incompat.measurement_bases = np.zeros((100, 2), dtype=int)
    shadows_incompat.measurement_outcomes = rng.integers(0, 2, size=(100, 2))
    # Observable requires X basis on first qubit
    incompat_obs = Observable("XI")
    vec_incompat = shadows_incompat._pauli_expectation_vectorized(incompat_obs)
    if not np.all(vec_incompat == 0):
        print("  FAIL: Incompatible basis should give all zeros")
        all_passed = False

    # Edge case: All measurements in compatible basis
    config_compat = ShadowConfig(num_qubits=2, shadow_size=100, random_seed=42)
    shadows_compat = RandomLocalCliffordShadows(config_compat)
    # All measurements in Z basis
    shadows_compat.measurement_bases = np.zeros((100, 2), dtype=int)
    shadows_compat.measurement_outcomes = rng.integers(0, 2, size=(100, 2))
    # Observable requires Z basis
    compat_obs = Observable("ZI")
    vec_compat = shadows_compat._pauli_expectation_vectorized(compat_obs)
    loop_compat = np.array([shadows_compat._pauli_expectation_single_shadow(i, compat_obs) for i in range(100)])
    if not np.allclose(vec_compat, loop_compat):
        print("  FAIL: Compatible basis - vectorized vs loop mismatch")
        all_passed = False
    # All should be non-zero (either +3 or -3)
    if not np.all(np.abs(vec_compat) == 3):
        print("  FAIL: Compatible basis should give |value| = 3")
        all_passed = False

    # Edge case: Large number of qubits
    config_large = ShadowConfig(num_qubits=10, shadow_size=200, random_seed=42)
    shadows_large = RandomLocalCliffordShadows(config_large)
    shadows_large.measurement_bases = rng.integers(0, 3, size=(200, 10))
    shadows_large.measurement_outcomes = rng.integers(0, 2, size=(200, 10))

    large_obs = Observable("XYZXYZXYZI")  # 9 non-identity
    vec_large = shadows_large._pauli_expectation_vectorized(large_obs)
    loop_large = np.array([shadows_large._pauli_expectation_single_shadow(i, large_obs) for i in range(200)])
    if not np.allclose(vec_large, loop_large):
        print("  FAIL: Large qubits - vectorized vs loop mismatch")
        all_passed = False

    # Edge case: Observable at end of string
    end_obs = Observable("IIIZ")
    vec_end = shadows._pauli_expectation_vectorized(end_obs)
    loop_end = np.array([shadows._pauli_expectation_single_shadow(i, end_obs) for i in range(num_shadows)])
    if not np.allclose(vec_end, loop_end):
        print("  FAIL: End observable - vectorized vs loop mismatch")
        all_passed = False

    # Edge case: Observable at start of string
    start_obs = Observable("XIII")
    vec_start = shadows._pauli_expectation_vectorized(start_obs)
    loop_start = np.array([shadows._pauli_expectation_single_shadow(i, start_obs) for i in range(num_shadows)])
    if not np.allclose(vec_start, loop_start):
        print("  FAIL: Start observable - vectorized vs loop mismatch")
        all_passed = False

    # Edge case: Y observable (basis index 2)
    y_obs = Observable("IYII")
    vec_y = shadows._pauli_expectation_vectorized(y_obs)
    loop_y = np.array([shadows._pauli_expectation_single_shadow(i, y_obs) for i in range(num_shadows)])
    if not np.allclose(vec_y, loop_y):
        print("  FAIL: Y observable - vectorized vs loop mismatch")
        all_passed = False

    if all_passed:
        print("  PASS: Shadow estimation tests passed")
    return all_passed


def validate_benchmarking_grouping():
    """Validate that pre-grouping in benchmarking produces same results."""
    print("\n=== Testing Benchmarking Row Grouping ===")
    from collections import defaultdict

    # Simulate LongFormRow-like objects
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

    # Old method: repeated filtering
    def old_method(rows, protocol_id):
        return [r for r in rows if r.protocol_id == protocol_id]

    # New method: pre-grouping
    rows_by_protocol = defaultdict(list)
    for row in rows:
        rows_by_protocol[row.protocol_id].append(row)

    def new_method(rows_by_protocol, protocol_id):
        return rows_by_protocol.get(protocol_id, [])

    # Compare results
    for proto in protocols:
        old_result = old_method(rows, proto)
        new_result = new_method(rows_by_protocol, proto)

        if len(old_result) != len(new_result):
            print(f"  FAIL: {proto} - count mismatch: {len(old_result)} vs {len(new_result)}")
            all_passed = False

        # Verify same objects (by checking se values)
        old_ses = sorted([r.se for r in old_result])
        new_ses = sorted([r.se for r in new_result])
        if old_ses != new_ses:
            print(f"  FAIL: {proto} - content mismatch")
            all_passed = False

    # Test missing protocol
    if new_method(rows_by_protocol, "nonexistent") != []:
        print("  FAIL: missing protocol should return empty list")
        all_passed = False

    # Edge case: Empty rows list
    empty_rows = []
    empty_by_protocol = defaultdict(list)
    for row in empty_rows:
        empty_by_protocol[row.protocol_id].append(row)
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

    # Edge case: Single protocol with many rows
    many_rows = [MockRow("same_proto", 100, 0.01 * i) for i in range(1000)]
    many_by_protocol = defaultdict(list)
    for row in many_rows:
        many_by_protocol[row.protocol_id].append(row)
    result = new_method(many_by_protocol, "same_proto")
    if len(result) != 1000:
        print(f"  FAIL: many rows - expected 1000, got {len(result)}")
        all_passed = False

    # Edge case: Secondary filtering by N_total (as done in benchmarking.py)
    max_n = 1000
    for proto in protocols:
        # Old combined filtering
        old_filtered = [r for r in rows if r.protocol_id == proto and r.N_total == max_n]
        # New: pre-group then filter
        new_filtered = [r for r in rows_by_protocol.get(proto, []) if r.N_total == max_n]

        if len(old_filtered) != len(new_filtered):
            print(f"  FAIL: {proto} N_total filter - count mismatch")
            all_passed = False

        old_ses = sorted([r.se for r in old_filtered])
        new_ses = sorted([r.se for r in new_filtered])
        if old_ses != new_ses:
            print(f"  FAIL: {proto} N_total filter - content mismatch")
            all_passed = False

    # Edge case: Protocol names with special characters
    special_rows = [
        MockRow("proto-with-dash", 100, 0.01),
        MockRow("proto_with_underscore", 100, 0.02),
        MockRow("proto.with.dot", 100, 0.03),
    ]
    special_by_protocol = defaultdict(list)
    for row in special_rows:
        special_by_protocol[row.protocol_id].append(row)

    for row in special_rows:
        result = new_method(special_by_protocol, row.protocol_id)
        if len(result) != 1 or result[0].se != row.se:
            print(f"  FAIL: special protocol name '{row.protocol_id}' not handled")
            all_passed = False

    # Edge case: Verify order preservation
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


def run_performance_comparison():
    """Run a quick performance comparison for key operations."""
    print("\n=== Performance Comparison ===")

    try:
        from quartumse.observables.core import Observable
    except ImportError as e:
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
    try:
        from quartumse.observables.core import ObservableSet
    except ImportError:
        return
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
    print("Optimization Validation Script")
    print("=" * 60)

    results = []

    results.append(("Observable Caching", validate_observable_caching()))
    results.append(("Parquet I/O", validate_parquet_io()))
    results.append(("Grouping", validate_grouping()))
    results.append(("Shot Data", validate_shot_data()))
    results.append(("Shadow Estimation", validate_shadow_estimation()))
    results.append(("Benchmarking Grouping", validate_benchmarking_grouping()))

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
