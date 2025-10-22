#!/usr/bin/env python3
import os
from pathlib import Path
from qiskit import QuantumCircuit, transpile
from quartumse.connectors import resolve_backend
from quartumse.shadows.core import Observable
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.reporting.manifest import MitigationConfig

def two_bell_circuit():
    qc = QuantumCircuit(4)
    qc.h(0); qc.cx(0,1)
    qc.h(2); qc.cx(2,3)
    return qc

def rot(circ, pauli):
    c = circ.copy()
    for i,p in enumerate(pauli):
        if p == "X":
            c.h(i)
        elif p == "Y":
            c.sdg(i); c.h(i)
    c.measure_all()
    return c

def parity(counts, pauli, shots):
    tot = 0.0
    for b, ct in counts.items():
        p = ct/shots
        par = 1.0
        for i, ch in enumerate(pauli):
            if ch != "I":
                bit = int(b[-(i+1)])
                par *= (1-2*bit)
        tot += p*par
    return tot

def main():
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        print("Error: QISKIT_IBM_TOKEN not set"); return 1
    backend, _ = resolve_backend("ibm:ibm_torino")
    Path("validation_data").mkdir(exist_ok=True)
    qc = two_bell_circuit()

    obs = [
        Observable("ZZII", 1.0), Observable("XXII", 1.0),
        Observable("IIZZ", 1.0), Observable("IIXX", 1.0)
    ]

    # Direct: measure ZZ and XX separately
    for basis, sels, shots in [("Z", ["ZZII","IIZZ"], 600), ("X", ["XXII","IIXX"], 600)]:
        circ = rot(qc, basis*4)
        tc = transpile(circ, backend)
        result = backend.run(tc, shots=shots).result()
        counts = result.get_counts()
        for o in obs:
            s = o.pauli_string
            if s in sels:
                val = parity(counts, s, shots)
                print(f"[Direct] {s}: {val:.3f} (shots={shots})")

    # Shadows v0
    sh0 = ShadowEstimator(backend="ibm:ibm_torino",
                          shadow_config=ShadowConfig(version=ShadowVersion.V0_BASELINE, shadow_size=2500, random_seed=1),
                          data_dir="validation_data")
    r0 = sh0.estimate(qc, obs, save_manifest=True)
    for k,v in r0.observables.items():
        print(f"[v0] {k}: {float(v['expectation_value']):.3f}")

    # Shadows v1 + MEM
    sh1 = ShadowEstimator(backend="ibm:ibm_torino",
                          shadow_config=ShadowConfig(version=ShadowVersion.V1_NOISE_AWARE, shadow_size=1500, random_seed=2, apply_inverse_channel=True),
                          mitigation_config=MitigationConfig(techniques=[], parameters={"mem_shots": 256}),
                          data_dir="validation_data")
    r1 = sh1.estimate(qc, obs, save_manifest=True)
    for k,v in r1.observables.items():
        print(f"[v1+MEM] {k}: {float(v['expectation_value']):.3f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
