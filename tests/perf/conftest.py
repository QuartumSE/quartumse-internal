"""Performance test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit

from quartumse.observables import Observable, ObservableSet

BASELINE_PATH = Path(__file__).parent / "perf_baseline.json"


@pytest.fixture(scope="session")
def perf_baseline() -> dict:
    """Load the committed performance baseline."""
    if not BASELINE_PATH.exists():
        pytest.skip("No perf_baseline.json found — run scripts/update_perf_baseline.py first")
    with open(BASELINE_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def perf_workload():
    """Build the standard 4-qubit workload matching scripts/perf_regression.py."""
    # 4-qubit circuit: Bell pair on (0,1) + Bell pair on (2,3)
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, 1)
    qc.h(2)
    qc.cx(2, 3)

    # 20 random Pauli observables (deterministic seed)
    rng = np.random.default_rng(12345)
    paulis = ["I", "X", "Y", "Z"]
    obs_list = []
    for i in range(20):
        ps = "".join(rng.choice(paulis) for _ in range(4))
        if ps == "IIII":
            ps = "ZIII"
        obs_list.append(Observable(observable_id=f"o{i:02d}", pauli_string=ps, coefficient=1.0))
    obs_set = ObservableSet(observables=obs_list)

    # Ground truth via statevector
    try:
        from quartumse.backends.truth import compute_ground_truth

        ground_truth = compute_ground_truth(qc, obs_set)
    except Exception:
        ground_truth = {o.observable_id: 0.0 for o in obs_list}

    # Raw pauli strings for ObservableSet construction benchmark
    rng2 = np.random.default_rng(12345)
    paulis_raw = []
    for _ in range(20):
        ps = "".join(rng2.choice(paulis) for _ in range(4))
        if ps == "IIII":
            ps = "ZIII"
        paulis_raw.append(ps)

    return {
        "circuit": qc,
        "obs_set": obs_set,
        "ground_truth": ground_truth,
        "paulis_raw": paulis_raw,
    }
