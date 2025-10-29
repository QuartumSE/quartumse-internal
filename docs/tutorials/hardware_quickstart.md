# Hardware Quickstart (IBM Runtime)

> Prereqs: `pip install quartumse[mitigation] qiskit-ibm-runtime`, IBM Quantum account, `export QISKIT_IBM_TOKEN=...`.

## 1) Verify credentials and quota
```bash
quartumse runtime-status --backend ibm:ibmq_qasm_simulator
```

## 2) Run S-T01 on IBM simulator
```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend ibm:ibmq_qasm_simulator
```

## 3) Enable MEM (v1) and compare
```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend ibm:ibmq_qasm_simulator --variant st02
```

## 4) Outputs

Manifests under `data/manifests/`, shots under `data/shots/`. See the [Manifest Schema](../explanation/manifest-schema.md).
