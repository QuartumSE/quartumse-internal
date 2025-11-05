#!/usr/bin/env python3
"""Quick hardware test on IBM quantum backend."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from qiskit import QuantumCircuit

def create_ghz_3qubit():
    """Create 3-qubit GHZ state."""
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(0, 2)
    return qc

def main():
    backend_name = "ibm_fez"  # Lowest queue
    print(f"=" * 80)
    print(f"QuartumSE Hardware Test - {backend_name}")
    print(f"=" * 80)

    # Create circuit
    circuit = create_ghz_3qubit()
    print(f"\nCircuit: 3-qubit GHZ state")
    print(f"Depth: {circuit.depth()}")

    # Define observables
    observables = [
        Observable("ZII"),
        Observable("ZZI"),
        Observable("ZIZ"),
    ]
    print(f"\nObservables: {[str(o) for o in observables]}")

    # Create estimator with v0 baseline (faster, no calibration needed)
    print(f"\nBackend: ibm:{backend_name}")
    print(f"Shadow version: v0 (baseline)")
    print(f"Shadow size: 100 (reduced for fast test)")

    estimator = ShadowEstimator(
        backend=f"ibm:{backend_name}",
        shadow_config=ShadowConfig(
            version=ShadowVersion.V0_BASELINE,
            shadow_size=100,  # Small for quick test
            random_seed=42,
        ),
        data_dir="data"
    )

    # Run estimation
    print("\nSubmitting job to IBM Quantum...")
    result = estimator.estimate(
        circuit=circuit,
        observables=observables,
        save_manifest=True,
    )

    # Display results
    print(f"\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Execution time: {result.execution_time:.2f}s")
    print(f"Shots used: {result.shots_used}")
    print(f"Manifest: {result.manifest_path}")
    print(f"\nObservable estimates:")

    for obs_str, obs_data in result.observables.items():
        exp_val = obs_data['expectation_value']
        ci = obs_data.get('ci_95', (None, None))
        print(f"  {obs_str}: {exp_val:.4f} ± CI: [{ci[0]:.4f}, {ci[1]:.4f}]")

    print(f"\n" + "=" * 80)
    print("✓ Hardware test completed successfully!")
    print("=" * 80)

    return 0

if __name__ == "__main__":
    exit(main())
