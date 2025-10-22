#!/usr/bin/env python3
import os, json, time
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit, transpile
from quartumse.connectors import resolve_backend, is_ibm_runtime_backend, create_runtime_sampler
from quartumse.shadows.core import Observable
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.reporting.manifest import MitigationConfig

def ghz_circuit(n=4):
    qc = QuantumCircuit(n)
    qc.h(0)
    for i in range(n-1):
        qc.cx(i, i+1)
    return qc

def rot_to_basis(circ, pauli):
    c = circ.copy()
    for i, p in enumerate(pauli):
        if p == "X":
            c.h(i)
        elif p == "Y":
            c.sdg(i); c.h(i)
    c.measure_all()
    return c

def exp_from_counts(counts, pauli, shots):
    tot = 0.0
    for b, ct in counts.items():
        p = ct/shots
        par = 1.0
        for i,ch in enumerate(pauli):
            if ch != "I":
                bit = int(b[-(i+1)])
                par *= (1-2*bit)
        tot += p*par
    return tot

def main():
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        print("Error: QISKIT_IBM_TOKEN not set"); return 1
    backend, snap = resolve_backend("ibm:ibm_torino")
    Path("validation_data").mkdir(exist_ok=True)
    n = 4  # adjust to 5 if coherence/connectivity allows
    qc = ghz_circuit(n)

    # Observables: pairwise ZZ and full X...X
    obs = []
    for i in range(n-1):
        s = ["I"]*n
        s[i]="Z"; s[i+1]="Z"
        obs.append(Observable("".join(s), 1.0))
    obs.append(Observable("".join(["X"]*n), 1.0))

    # Direct grouped (ZZ in Z basis, XXXX in X basis)
    direct_specs = [
        ("ZZs", rot_to_basis(qc, "Z"*n), [o for o in obs if "X" not in str(o)]),
        ("XXXX", rot_to_basis(qc, "X"*n), [o for o in obs if "X" in str(o)]),
    ]
    shots = [1200, 1200]
    direct_results = {}

    sampler = None
    if is_ibm_runtime_backend(backend):
        sampler = create_runtime_sampler(backend)

    for (label, circ, olist), s in zip(direct_specs, shots):
        tc = transpile(circ, backend)

        if sampler is not None:
            job = sampler.run([tc], shots=s)
            result = job.result()
            counts = result[0].data.meas.get_counts()
        else:
            job = backend.run(tc, shots=s)
            counts = job.result().get_counts()

        for o in olist:
            pauli = o.pauli_string
            if "X" in pauli:
                # Measured in X basis already by rotation
                pass
            exp = exp_from_counts(counts, pauli, s)
            direct_results[str(o)] = {"expectation": float(exp), "shots": s}

    # Shadows v0
    sh0 = ShadowEstimator(
        backend="ibm:ibm_torino",
        shadow_config=ShadowConfig(version=ShadowVersion.V0_BASELINE, shadow_size=3000, random_seed=7),
        data_dir="validation_data"
    )
    r0 = sh0.estimate(qc, obs, save_manifest=True)
    res_v0 = {k: {"expectation": float(v["expectation_value"]), "ci": v.get("ci_95")} for k,v in r0.observables.items()}

    # Shadows v1 + MEM
    mem_shots = 256
    sh1 = ShadowEstimator(
        backend="ibm:ibm_torino",
        shadow_config=ShadowConfig(version=ShadowVersion.V1_NOISE_AWARE, shadow_size=1500, random_seed=11, apply_inverse_channel=True),
        mitigation_config=MitigationConfig(techniques=[], parameters={"mem_shots": mem_shots}),
        data_dir="validation_data"
    )
    r1 = sh1.estimate(qc, obs, save_manifest=True)
    res_v1 = {k: {"expectation": float(v["expectation_value"]), "ci": v.get("ci_95")} for k,v in r1.observables.items()}

    # Print summary
    for o in obs:
        k = str(o)
        print(f"{k:>s} | Direct: {direct_results.get(k,{}).get('expectation',float('nan')): .3f} "
              f"| v0: {res_v0.get(k,{}).get('expectation',float('nan')): .3f} "
              f"| v1: {res_v1.get(k,{}).get('expectation',float('nan')): .3f}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
