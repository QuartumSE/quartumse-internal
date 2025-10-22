#!/usr/bin/env python3
import os
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.circuit.library import RXGate, RZGate
from quartumse.connectors import resolve_backend
from quartumse.shadows.core import Observable
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.reporting.manifest import MitigationConfig

def trotter_ising(n=6, J=1.0, h=1.0, dt=0.2, steps=1):
    qc = QuantumCircuit(n)
    # start in |000...>
    for _ in range(steps):
        # exp(-i J dt Z_i Z_{i+1})
        for i in range(n-1):
            qc.cx(i, i+1); qc.rz(2*J*dt, i+1); qc.cx(i, i+1)
        # exp(-i h dt X_i)
        for i in range(n):
            qc.rx(2*h*dt, i)
    return qc

def make_observables_ising(n=6):
    obs = []
    # Z_i Z_{i+1}
    for i in range(n-1):
        s = ["I"]*n
        s[i]="Z"; s[i+1]="Z"
        obs.append(Observable("".join(s), 1.0))
    # X_i
    for i in range(n):
        s = ["I"]*n
        s[i]="X"
        obs.append(Observable("".join(s), 1.0))
    return obs

def main():
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        print("Error: QISKIT_IBM_TOKEN not set"); return 1
    backend, _ = resolve_backend("ibm:ibm_torino")
    Path("validation_data").mkdir(exist_ok=True)

    n=6
    qc = trotter_ising(n=n, J=1.0, h=0.8, dt=0.15, steps=1)
    obs = make_observables_ising(n=n)

    # Shadows v0 and v1+MEM for all terms
    sh0 = ShadowEstimator(backend="ibm:ibm_torino",
                          shadow_config=ShadowConfig(version=ShadowVersion.V0_BASELINE, shadow_size=3000, random_seed=9),
                          data_dir="validation_data")
    r0 = sh0.estimate(qc, obs, save_manifest=True)
    print(f"[Ising v0] Estimated {len(r0.observables)} terms.")

    sh1 = ShadowEstimator(backend="ibm:ibm_torino",
                          shadow_config=ShadowConfig(version=ShadowVersion.V1_NOISE_AWARE, shadow_size=3000, random_seed=10, apply_inverse_channel=True),
                          mitigation_config=MitigationConfig(techniques=[], parameters={"mem_shots": 128}),
                          data_dir="validation_data")
    r1 = sh1.estimate(qc, obs, save_manifest=True)
    print(f"[Ising v1+MEM] Estimated {len(r1.observables)} terms.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
