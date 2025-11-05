#!/usr/bin/env python3
"""Check available IBM quantum backends."""

import os
from pathlib import Path
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

token = os.environ.get('QISKIT_IBM_TOKEN')
if not token:
    print("Error: QISKIT_IBM_TOKEN not set in .env file")
    exit(1)

# Initialize service
service = QiskitRuntimeService(token=token)

# Get backends
backends = service.backends(simulator=False, operational=True)
sorted_backends = sorted(backends, key=lambda x: x.status().pending_jobs)

print(f"Available IBM Quantum Backends ({len(sorted_backends)} total):\n")
print(f"{'Backend':<20} {'Qubits':<8} {'Pending Jobs':<15} {'Status'}")
print("-" * 70)

for backend in sorted_backends[:15]:
    status = backend.status()
    print(f"{backend.name:<20} {backend.num_qubits:<8} {status.pending_jobs:<15} {status.status_msg}")

print("\nRecommendation: Choose a backend with low pending jobs for faster execution")
