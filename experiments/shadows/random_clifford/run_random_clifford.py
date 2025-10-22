#!/usr/bin/env python3
import os, random
from pathlib import Path
from qiskit import QuantumCircuit
from quartumse.connectors import resolve_backend
from quartumse.shadows.core import Observable
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.reporting.manifest import MitigationConfig

def random_clifford_circuit(n=5, depth=10, seed=123):
    import numpy as np
    rng = np.random.default_rng(seed)
    qc = QuantumCircuit(n)
    # Simple pseudo-Clifford-ish sampler (H,S,CX)
    for _ in range(depth):
        for q in range(n):
            gate = rng.integers(0,3)
            if gate == 0: qc.h(q)
            elif gate == 1: qc.s(q)
        # random CX
        for _ in range(n//2):
            a, b = rng.integers(0,n,2)
            if a != b:
                qc.cx(int(a), int(b))
    return qc

def pauli_strings(n, k=50, seed=22):
    import numpy as np
    rng = np.random.default_rng(seed)
    P = ['I','X','Y','Z']
    out = set()
    while len(out) < k:
        s = ''.join(rng.choice(P, size=n))
        if s != 'I'*n:
            out.add(s)
    return [Observable(s, 1.0) for s in sorted(list(out))]

def main():
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        print("Error: QISKIT_IBM_TOKEN not set"); return 1
    backend, _ = resolve_backend("ibm:ibm_torino")
    Path("validation_data").mkdir(exist_ok=True)

    n=5
    qc = random_clifford_circuit(n=n, depth=10, seed=123)
    observables = pauli_strings(n, k=60, seed=22)

    # Shadows v0
    sh0 = ShadowEstimator(backend="ibm:ibm_torino",
                          shadow_config=ShadowConfig(version=ShadowVersion.V0_BASELINE, shadow_size=5000, random_seed=4),
                          data_dir="validation_data")
    r0 = sh0.estimate(qc, observables, save_manifest=True)
    print(f"v0 estimated {len(r0.observables)} observables.")

    # Shadows v1 + MEM
    sh1 = ShadowEstimator(backend="ibm:ibm_torino",
                          shadow_config=ShadowConfig(version=ShadowVersion.V1_NOISE_AWARE, shadow_size=3000, random_seed=5, apply_inverse_channel=True),
                          mitigation_config=MitigationConfig(techniques=[], parameters={"mem_shots": 128}),
                          data_dir="validation_data")
    r1 = sh1.estimate(qc, observables, save_manifest=True)
    print(f"v1+MEM estimated {len(r1.observables)} observables.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
