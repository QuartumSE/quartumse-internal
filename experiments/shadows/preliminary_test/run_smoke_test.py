#!/usr/bin/env python3
import os, time, json
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from quartumse.connectors import resolve_backend
from quartumse.shadows.core import Observable
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.reporting.manifest import MitigationConfig

def bell_circuit():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0,1)
    return qc

def measure_in_basis(qc, pauli_str):
    c = qc.copy()
    for i, p in enumerate(pauli_str):
        if p == "X":
            c.h(i)
        elif p == "Y":
            c.sdg(i); c.h(i)
    c.measure_all()
    return c

def parity_from_counts(counts, pauli_str, shots):
    def bit(bstr, i): return int(bstr[-(i+1)])
    tot = 0.0
    for b, ct in counts.items():
        p = ct/shots
        par = 1.0
        for i, ch in enumerate(pauli_str):
            if ch != "I":
                par *= (1 - 2*bit(b, i))
        tot += p*par
    return tot

def run():
    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        print("Error: QISKIT_IBM_TOKEN not set"); return 1

    # Initialize service and backend
    service = QiskitRuntimeService(token=token)
    backend = service.backend("ibm_torino")
    print("Connected to:", backend.name)
    Path("validation_data").mkdir(exist_ok=True)
    qc = bell_circuit()

    observables = [Observable("ZZ", 1.0), Observable("XX", 1.0)]

    # --- Direct measurement using Sampler primitive ---
    direct_shots = [250, 250]
    res_direct = {}
    sampler = Sampler(mode=backend)

    for obs, shots in zip(observables, direct_shots):
        c = measure_in_basis(qc, obs.pauli_string)
        tc = transpile(c, backend)

        # Use Sampler primitive
        job = sampler.run([tc], shots=shots)
        result = job.result()

        # Extract counts from SamplerV2 result
        pub_result = result[0]
        counts_array = pub_result.data.meas.get_counts()

        exp = parity_from_counts(counts_array, obs.pauli_string, shots)
        res_direct[str(obs)] = {"expectation": float(exp), "shots": shots}
        print(f"[Direct] {obs}: {exp:.3f} (shots={shots})")

    # --- Shadows v0 ---
    sh0 = ShadowEstimator(
        backend="ibm:ibm_torino",
        shadow_config=ShadowConfig(version=ShadowVersion.V0_BASELINE, shadow_size=500, random_seed=42),
        data_dir="validation_data"
    )
    r0 = sh0.estimate(qc, observables, save_manifest=True)
    res_v0 = {k: {"expectation": float(v["expectation_value"]), "ci": v.get("ci_95")} for k,v in r0.observables.items()}
    print("[Shadows v0] done.")

    # --- Shadows v1 + MEM ---
    mem_shots = 128
    sh1 = ShadowEstimator(
        backend="ibm:ibm_torino",
        shadow_config=ShadowConfig(version=ShadowVersion.V1_NOISE_AWARE, shadow_size=200, random_seed=43, apply_inverse_channel=True),
        mitigation_config=MitigationConfig(techniques=[], parameters={"mem_shots": mem_shots}),
        data_dir="validation_data"
    )
    r1 = sh1.estimate(qc, observables, save_manifest=True)
    res_v1 = {k: {"expectation": float(v["expectation_value"]), "ci": v.get("ci_95")} for k,v in r1.observables.items()}
    print("[Shadows v1+MEM] done.")

    # Summary
    def fmt_ci(ci):
        return "N/A" if ci is None else f"[{ci[0]:.3f}, {ci[1]:.3f}]"
    for obs in observables:
        o = str(obs)
        print(f"\nObservable: {o}")
        print("  Direct    :", f"{res_direct[o]['expectation']:.3f}")
        print("  Shadows v0:", f"{res_v0[o]['expectation']:.3f}", "CI:", fmt_ci(res_v0[o].get("ci")))
        print("  Shadows v1:", f"{res_v1[o]['expectation']:.3f}", "CI:", fmt_ci(res_v1[o].get("ci")))

    return 0

if __name__ == "__main__":
    raise SystemExit(run())
