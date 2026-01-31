"""Generate a comprehensive circuit guide with diagrams for all 12 benchmark circuits."""

import base64
from io import BytesIO
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit


# =============================================================================
# Circuit Builders (from benchmark notebook)
# =============================================================================

def build_ghz(n_qubits: int) -> QuantumCircuit:
    """GHZ state: |00...0> + |11...1> / sqrt(2)"""
    qc = QuantumCircuit(n_qubits, name=f'GHZ_{n_qubits}q')
    qc.h(0)
    for i in range(1, n_qubits):
        qc.cx(i - 1, i)
    return qc

def build_bell_pairs(n_pairs: int) -> QuantumCircuit:
    """Parallel Bell pairs."""
    n_qubits = 2 * n_pairs
    qc = QuantumCircuit(n_qubits, name=f'Bell_{n_pairs}pairs')
    for i in range(n_pairs):
        qc.h(2 * i)
        qc.cx(2 * i, 2 * i + 1)
    return qc

def build_ising_trotter(n_qubits: int, steps: int = 3, dt: float = 0.5) -> QuantumCircuit:
    """Trotterized transverse-field Ising model."""
    qc = QuantumCircuit(n_qubits, name=f'Ising_{n_qubits}q_t{steps}')
    J, h = 1.0, 0.5
    for q in range(n_qubits):
        qc.h(q)
    for _ in range(steps):
        for q in range(n_qubits - 1):
            qc.cx(q, q + 1)
            qc.rz(2 * J * dt, q + 1)
            qc.cx(q, q + 1)
        for q in range(n_qubits):
            qc.rx(2 * h * dt, q)
    return qc

def build_h2_ansatz(theta: float = 0.5) -> QuantumCircuit:
    """H2 molecule ansatz (4 qubits)."""
    qc = QuantumCircuit(4, name='H2_ansatz')
    qc.x(0); qc.x(1)
    qc.cx(1, 2); qc.ry(theta, 2); qc.cx(1, 2)
    qc.cx(0, 3); qc.ry(theta / 2, 3); qc.cx(0, 3)
    return qc

def build_lih_ansatz(theta: float = 0.5) -> QuantumCircuit:
    """LiH molecule ansatz (6 qubits)."""
    qc = QuantumCircuit(6, name='LiH_ansatz')
    qc.x(0); qc.x(1)
    for i in range(3):
        qc.cx(i, i + 1)
        qc.ry(theta * (i + 1) / 3, i + 1)
        qc.cx(i, i + 1)
    qc.cx(3, 4); qc.ry(theta / 2, 4); qc.cx(3, 4)
    qc.cx(4, 5); qc.ry(theta / 3, 5); qc.cx(4, 5)
    return qc

def build_qaoa_maxcut_ring(n_qubits: int, p: int = 1, gamma: float = 0.5, beta: float = 0.5) -> QuantumCircuit:
    """QAOA for MAX-CUT on ring graph."""
    qc = QuantumCircuit(n_qubits, name=f'QAOA_ring_{n_qubits}q_p{p}')
    for q in range(n_qubits): qc.h(q)
    for _ in range(p):
        for q in range(n_qubits):
            q_next = (q + 1) % n_qubits
            qc.cx(q, q_next); qc.rz(2 * gamma, q_next); qc.cx(q, q_next)
        for q in range(n_qubits): qc.rx(2 * beta, q)
    return qc

def build_ghz_phase_sensing(n_qubits: int, phi: float = 0.1) -> QuantumCircuit:
    """GHZ state with phase encoding."""
    qc = build_ghz(n_qubits)
    qc.name = f'GHZ_phase_{n_qubits}q'
    for q in range(n_qubits): qc.rz(phi, q)
    return qc


# =============================================================================
# Circuit Definitions with Metadata
# =============================================================================

CIRCUITS = {
    "S-GHZ-4": {
        "name": "4-Qubit GHZ State",
        "family": "Shadows Core",
        "family_code": "S",
        "qubits": 4,
        "builder": lambda: build_ghz(4),
        "short_desc": "Maximally entangled 4-qubit Greenberger-Horne-Zeilinger state",
        "description": """
The GHZ state is a fundamental quantum state that exhibits genuine multipartite entanglement.
For 4 qubits, it creates the superposition: |GHZ₄⟩ = (|0000⟩ + |1111⟩) / √2

This state is the quantum analogue of a "cat state" - all qubits are either all 0 or all 1,
in perfect superposition. Unlike classical correlations, measuring any single qubit instantly
determines the state of all others.""",
        "physics": """
**Mathematical Form:** |GHZ₄⟩ = (|0000⟩ + |1111⟩) / √2

**Key Properties:**
- Maximum multipartite entanglement (cannot be written as product of smaller states)
- Stabilized by operators: XXXX, ZZII, IZZI, IIZZ
- Violates Bell inequalities by maximal amount (Mermin inequality)
- Single-qubit decoherence destroys entire state""",
        "applications": """
- **Quantum Error Correction:** Basis for many QEC codes
- **Quantum Metrology:** Enhanced phase sensitivity (Heisenberg limit)
- **Quantum Communication:** Secret sharing protocols
- **Bell Tests:** Demonstrating genuine multipartite nonlocality""",
        "importance": """
GHZ states are essential benchmarks because they test a quantum computer's ability to create
and maintain genuine multipartite entanglement. Classical shadows must correctly estimate
multi-qubit correlations (like ⟨XXXX⟩) which require all shadows to align."""
    },

    "S-GHZ-5": {
        "name": "5-Qubit GHZ State",
        "family": "Shadows Core",
        "family_code": "S",
        "qubits": 5,
        "builder": lambda: build_ghz(5),
        "short_desc": "Maximally entangled 5-qubit GHZ state",
        "description": """
Extension of the GHZ state to 5 qubits: |GHZ₅⟩ = (|00000⟩ + |11111⟩) / √2

The 5-qubit version adds complexity because:
1. More stabilizer operators to verify (XXXXX, plus 4 ZZ pairs)
2. Larger Hilbert space (32 dimensions vs 16)
3. More challenging for classical shadow estimation due to increased locality""",
        "physics": """
**Mathematical Form:** |GHZ₅⟩ = (|00000⟩ + |11111⟩) / √2

**Stabilizer Group:**
- XXXXX (all X)
- ZZIII, IZZII, IIZZI, IIIZZ (adjacent ZZ pairs)

**Entanglement:** The state has maximal 5-party entanglement entropy.""",
        "applications": """
- **5-Qubit Error Correction:** The smallest code that can correct arbitrary single-qubit errors
- **Distributed Quantum Computing:** 5-party quantum secret sharing
- **Quantum Networks:** Conference key agreement protocols""",
        "importance": """
Tests scaling behavior of shadow estimation. The 3^k variance scaling means 5-qubit operators
like XXXXX have theoretical variance ≈ 243× higher than single-qubit operators."""
    },

    "S-BELL-2": {
        "name": "2 Bell Pairs",
        "family": "Shadows Core",
        "family_code": "S",
        "qubits": 4,
        "builder": lambda: build_bell_pairs(2),
        "short_desc": "Two independent Bell pairs (4 qubits total)",
        "description": """
Two independent maximally-entangled Bell pairs: |Φ⁺⟩₀₁ ⊗ |Φ⁺⟩₂₃

Each Bell pair is: |Φ⁺⟩ = (|00⟩ + |11⟩) / √2

Unlike GHZ states, Bell pairs have *bipartite* entanglement - qubits are entangled in pairs,
not globally. This creates a fundamentally different correlation structure.""",
        "physics": """
**State Structure:** |Ψ⟩ = |Φ⁺⟩₀₁ ⊗ |Φ⁺⟩₂₃ = ½(|0000⟩ + |0011⟩ + |1100⟩ + |1111⟩)

**Key Correlations:**
- Within pairs: ⟨ZZ⟩₀₁ = ⟨ZZ⟩₂₃ = +1, ⟨XX⟩₀₁ = ⟨XX⟩₂₃ = +1
- Cross-pairs: ⟨ZZ⟩₀₂ = ⟨ZZ⟩₁₃ = 0 (no correlation)

**Entanglement Structure:** Separable across the (01)|(23) partition""",
        "applications": """
- **Quantum Teleportation:** Each Bell pair can teleport one qubit
- **Superdense Coding:** Transmit 2 classical bits per qubit
- **Entanglement Distribution:** Building block for quantum networks
- **Crosstalk Detection:** Cross-pair correlations should be zero""",
        "importance": """
Critical for testing that shadow estimation correctly identifies correlation structure.
Must distinguish genuine two-qubit entanglement (within pairs) from no correlation (cross-pairs).
Any ⟨ZZ⟩₀₂ ≠ 0 indicates estimation error or physical crosstalk."""
    },

    "S-BELL-3": {
        "name": "3 Bell Pairs",
        "family": "Shadows Core",
        "family_code": "S",
        "qubits": 6,
        "builder": lambda: build_bell_pairs(3),
        "short_desc": "Three independent Bell pairs (6 qubits total)",
        "description": """
Three parallel Bell pairs on 6 qubits: |Φ⁺⟩₀₁ ⊗ |Φ⁺⟩₂₃ ⊗ |Φ⁺⟩₄₅

This tests shadow estimation on a structured 6-qubit state where entanglement is
localized to specific pairs. The challenge is maintaining precision as qubit count grows.""",
        "physics": """
**State:** |Ψ⟩ = |Φ⁺⟩₀₁ ⊗ |Φ⁺⟩₂₃ ⊗ |Φ⁺⟩₄₅

**Correlation Matrix (ZZ):**
|     | q0 | q1 | q2 | q3 | q4 | q5 |
|-----|----|----|----|----|----|----|
| q0  | 1  | 1  | 0  | 0  | 0  | 0  |
| q1  | 1  | 1  | 0  | 0  | 0  | 0  |
| q2  | 0  | 0  | 1  | 1  | 0  | 0  |
| ... |

Only ⟨ZZ⟩ within each pair is nonzero.""",
        "applications": """
- **Parallel Quantum Channels:** 3 independent quantum communication channels
- **Error Characterization:** Test spatial correlations in noise
- **Network Primitives:** Multiparty protocols requiring pairwise entanglement""",
        "importance": """
At 6 qubits, classical shadow variance becomes significant. This tests whether shadows
can still resolve the pair structure or if cross-pair noise appears."""
    },

    "S-ISING-4": {
        "name": "4-Qubit Ising Ground State",
        "family": "Shadows Core",
        "family_code": "S",
        "qubits": 4,
        "builder": lambda: build_ising_trotter(4, steps=3),
        "short_desc": "Trotterized transverse-field Ising model ground state",
        "description": """
Approximate ground state of the transverse-field Ising model (TFIM), prepared via
Trotterized time evolution.

The TFIM Hamiltonian: H = -J Σᵢ ZᵢZᵢ₊₁ - h Σᵢ Xᵢ

Starting from |+⟩^⊗n (ground state of -ΣXᵢ), we apply Trotter steps to evolve toward
the ground state of the full Hamiltonian.""",
        "physics": """
**Hamiltonian:** H = -J Σᵢ ZᵢZᵢ₊₁ - h Σᵢ Xᵢ  (here J=1.0, h=0.5)

**Trotter Step:**
1. Apply e^{-iJdt ZᵢZᵢ₊₁} for all adjacent pairs (ZZ interaction)
2. Apply e^{-ihdt Xᵢ} for all qubits (transverse field)

**Ground State Properties:**
- Strong ZZ correlations between neighbors: ⟨ZᵢZᵢ₊₁⟩ ≈ -0.9 to -1.0
- Nonzero magnetization: ⟨Xᵢ⟩ ≈ 0.3 to 0.5
- Entanglement across all qubits (but weaker than GHZ)""",
        "applications": """
- **Condensed Matter Physics:** Model for magnetic phase transitions
- **Quantum Simulation:** Benchmark for analog quantum simulators
- **VQE Preparation:** Target state for variational algorithms
- **Quantum Annealing:** Connection to adiabatic quantum computing""",
        "importance": """
Ising models have *local* correlations (nearest-neighbor ZZ) unlike GHZ (global correlations).
Classical shadows should efficiently estimate local observables with low variance."""
    },

    "S-ISING-6": {
        "name": "6-Qubit Ising Ground State",
        "family": "Shadows Core",
        "family_code": "S",
        "qubits": 6,
        "builder": lambda: build_ising_trotter(6, steps=3),
        "short_desc": "Larger Trotterized Ising ground state approximation",
        "description": """
6-qubit version of the transverse-field Ising ground state. With more qubits:
- Richer correlation structure (5 nearest-neighbor pairs)
- Approach to thermodynamic limit behavior
- Tests scaling of shadow estimation variance""",
        "physics": """
**Chain Structure:** 6 qubits in a line with 5 ZZ bonds

q0 -- q1 -- q2 -- q3 -- q4 -- q5

**Observable Sets:**
- Magnetization: ⟨Xᵢ⟩ for i=0..5
- NN correlations: ⟨ZᵢZᵢ₊₁⟩ for i=0..4
- Longer-range: ⟨ZᵢZⱼ⟩ decay with distance""",
        "applications": """
- **Quantum Phase Transitions:** Study critical behavior
- **Entanglement Area Law:** Ground states satisfy area law for entanglement
- **Quantum Many-Body Physics:** Benchmark for larger-scale simulations""",
        "importance": """
Tests whether classical shadows maintain accuracy for longer-range correlations
and whether the estimation variance grows acceptably with system size."""
    },

    "C-H2": {
        "name": "H₂ Molecule Ansatz",
        "family": "Chemistry",
        "family_code": "C",
        "qubits": 4,
        "builder": lambda: build_h2_ansatz(0.5),
        "short_desc": "Variational ansatz for hydrogen molecule ground state",
        "description": """
A hardware-efficient ansatz targeting the ground state of the H₂ molecule in the
STO-3G minimal basis. This is the "hydrogen atom" of quantum chemistry simulation.

The 4 qubits represent 4 spin-orbitals:
- q0, q1: 1s orbital (spin up/down)
- q2, q3: 1s* antibonding orbital (spin up/down)""",
        "physics": """
**Molecular Hamiltonian (Jordan-Wigner):**
H = Σᵢⱼ hᵢⱼ aᵢ†aⱼ + Σᵢⱼₖₗ gᵢⱼₖₗ aᵢ†aⱼ†aₖaₗ

After transformation, H contains ~15 Pauli terms with varying weights.

**Key Observables:**
- Energy: ⟨H⟩ = Σ cₐ⟨Pₐ⟩ where Pₐ are Pauli strings
- Particle number: ⟨N⟩ = Σᵢ⟨Zᵢ⟩
- Spin: ⟨S²⟩, ⟨Sᵤ⟩""",
        "applications": """
- **Variational Quantum Eigensolver (VQE):** Primary use case for near-term devices
- **Ground State Energy:** Compute binding curves, molecular properties
- **Quantum Chemistry Benchmarks:** Standard test for quantum advantage claims""",
        "importance": """
Chemistry applications require estimating many Pauli terms to compute the energy.
Classical shadows' ability to estimate multiple observables from one dataset is
ideal for this use case. Accuracy of energy estimation is the key metric."""
    },

    "C-LiH": {
        "name": "LiH Molecule Ansatz",
        "family": "Chemistry",
        "family_code": "C",
        "qubits": 6,
        "builder": lambda: build_lih_ansatz(0.5),
        "short_desc": "Variational ansatz for lithium hydride ground state",
        "description": """
A 6-qubit ansatz for the LiH molecule, a more complex molecular system than H₂.
LiH is ionic with partial charge transfer from Li to H.

The 6 qubits encode 6 spin-orbitals from a minimal basis set representation.
More orbitals means more Pauli terms in the Hamiltonian (~100+ terms).""",
        "physics": """
**Molecular Properties:**
- Bond length: ~1.6 Å at equilibrium
- Dipole moment: ~5.9 Debye
- Binding energy: ~2.5 eV

**Hamiltonian Complexity:**
The LiH Hamiltonian has O(100) Pauli terms, requiring efficient observable estimation.""",
        "applications": """
- **Beyond-H₂ Benchmarks:** Tests scalability to larger molecules
- **Ionic Systems:** Model for studying charge transfer
- **Active Space Methods:** Often used with CASSCF-like active spaces""",
        "importance": """
With ~100 Pauli observables, LiH tests whether classical shadows provide practical
advantage over direct measurement. The "measure once, estimate many" property should
reduce total shot count compared to measuring each term separately."""
    },

    "O-QAOA-5": {
        "name": "QAOA MAX-CUT (5-node Ring)",
        "family": "Optimization",
        "family_code": "O",
        "qubits": 5,
        "builder": lambda: build_qaoa_maxcut_ring(5, p=1),
        "short_desc": "Quantum Approximate Optimization for MAX-CUT on 5-node ring",
        "description": """
QAOA applied to the MAX-CUT problem on a 5-node ring graph. MAX-CUT asks: what is
the maximum number of edges that can be "cut" by partitioning vertices into two groups?

For a ring of 5 nodes, the optimal cut is 4 edges (alternating partition).""",
        "physics": """
**QAOA Ansatz:**
|ψ(γ,β)⟩ = e^{-iβ Σᵢ Xᵢ} e^{-iγ Σ_{ij} ZᵢZⱼ} |+⟩^⊗n

**Cost Hamiltonian (MAX-CUT):**
H_C = Σ_{edges} (1 - ZᵢZⱼ)/2

Measures how many edges connect different partitions.

**Mixer Hamiltonian:**
H_M = Σᵢ Xᵢ

Drives exploration of solution space.""",
        "applications": """
- **Combinatorial Optimization:** Scheduling, logistics, graph partitioning
- **Quantum Advantage Exploration:** Near-term algorithm for potential speedup
- **Hybrid Classical-Quantum:** Parameters optimized classically""",
        "importance": """
QAOA observables (ZᵢZⱼ terms) all commute, meaning grouped measurement is very efficient.
This tests whether classical shadows compete when observables have favorable structure."""
    },

    "O-QAOA-7": {
        "name": "QAOA MAX-CUT (7-node Ring)",
        "family": "Optimization",
        "family_code": "O",
        "qubits": 7,
        "builder": lambda: build_qaoa_maxcut_ring(7, p=1),
        "short_desc": "QAOA MAX-CUT on larger 7-node ring",
        "description": """
QAOA on a 7-node ring graph. At 7 qubits, the state space is 128-dimensional and
classical shadow variance begins to become significant.

The optimal MAX-CUT for a 7-ring is 6 edges (can't cut all 7 in a ring with odd nodes).""",
        "physics": """
**Graph Structure:** 7 nodes in a cycle, each connected to 2 neighbors
- Edges: (0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,0)

**Frustration:** With odd number of nodes, cannot achieve perfect alternating partition.
Best solution cuts 6 of 7 edges.

**QAOA State:** Encodes superposition over all 2^7 = 128 possible partitions""",
        "applications": """
- **Scalability Testing:** Does quantum advantage persist at larger sizes?
- **Frustration Effects:** Study of frustrated optimization landscapes
- **Parameter Landscape:** QAOA exhibits complex optimization landscapes""",
        "importance": """
At 7 qubits, the benchmark shows classical shadows having higher variance than direct
methods. This indicates a crossover point where shadow overhead becomes significant."""
    },

    "M-PHASE-3": {
        "name": "3-Qubit Phase Sensing",
        "family": "Metrology",
        "family_code": "M",
        "qubits": 3,
        "builder": lambda: build_ghz_phase_sensing(3, phi=0.1),
        "short_desc": "GHZ-enhanced quantum phase estimation",
        "description": """
A GHZ state with small phase rotations applied, designed for quantum-enhanced parameter
estimation. The state encodes a phase φ that can be estimated from measurements.

|ψ(φ)⟩ = (|000⟩ + e^{3iφ}|111⟩) / √2

The n-qubit GHZ state provides Heisenberg-limited scaling: Δφ ∝ 1/n instead of 1/√n.""",
        "physics": """
**Phase Encoding:**
Starting from GHZ: (|000⟩ + |111⟩)/√2
Apply Rz(φ) to each qubit: (|000⟩ + e^{3iφ}|111⟩)/√2

**Sensitivity:**
- Phase appears with factor n (number of qubits)
- Measurement of ⟨XXX⟩ or ⟨YYY⟩ reveals cos(3φ) or sin(3φ)
- Precision: Δφ ≥ 1/(n√M) (Heisenberg limit) vs 1/√(nM) (standard limit)""",
        "applications": """
- **Magnetometry:** Sensing magnetic fields with quantum enhancement
- **Gravitational Wave Detection:** LIGO-style interferometry improvements
- **Atomic Clocks:** Enhanced frequency standards
- **Quantum Radar:** Improved target detection""",
        "importance": """
Metrology applications require precise estimation of specific observables (like ⟨XXX⟩).
Classical shadows should provide unbiased estimates with controlled variance for these
critical quantities."""
    },

    "M-PHASE-4": {
        "name": "4-Qubit Phase Sensing",
        "family": "Metrology",
        "family_code": "M",
        "qubits": 4,
        "builder": lambda: build_ghz_phase_sensing(4, phi=0.1),
        "short_desc": "4-qubit GHZ-enhanced phase estimation",
        "description": """
4-qubit version of GHZ phase sensing. The phase factor increases to e^{4iφ}, providing
even better phase sensitivity.

|ψ(φ)⟩ = (|0000⟩ + e^{4iφ}|1111⟩) / √2

With 4 qubits, achieves 4× better phase resolution than a single qubit (at same shot count).""",
        "physics": """
**Enhanced Sensitivity:**
Phase sensitivity: dP/dφ ∝ n = 4

**Key Observables for Phase Extraction:**
- ⟨XXXX⟩ = cos(4φ)
- ⟨YYYY⟩ = cos(4φ)
- ⟨XYXY⟩ = cos(4φ)

All weight-4 Pauli strings with even Y count extract the phase.""",
        "applications": """
- **Precision Measurement:** Any scenario where parameters must be estimated
- **Phase Transitions:** Detecting small symmetry-breaking fields
- **Quantum Sensors:** Integration into sensing networks""",
        "importance": """
Tests shadow estimation of 4-local observables, where variance scaling (3^4 = 81) is
significant but still manageable. Good probe of intermediate locality regime."""
    }
}


def circuit_to_base64_image(qc: QuantumCircuit, style: str = "mpl") -> str:
    """Convert a quantum circuit to a base64-encoded PNG image."""
    try:
        fig = qc.draw(output="mpl", style={"backgroundcolor": "#FFFFFF"})
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
        buf.seek(0)
        import matplotlib.pyplot as plt
        plt.close(fig)
        return base64.b64encode(buf.read()).decode("utf-8")
    except Exception as e:
        return None


def generate_html_report(output_path: Path) -> None:
    """Generate a comprehensive HTML report with circuit diagrams."""

    # Collect circuit images
    circuit_images = {}
    for circuit_id, info in CIRCUITS.items():
        qc = info["builder"]()
        img_data = circuit_to_base64_image(qc)
        circuit_images[circuit_id] = img_data
        print(f"Generated diagram for {circuit_id}")

    # Generate HTML
    html_parts = ["""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>QuartumSE Benchmark Circuits - Complete Guide</title>
    <style>
        @page { size: A4; margin: 2cm; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            line-height: 1.7;
            color: #2c3e50;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            font-size: 2.2em;
        }
        h2 {
            color: #34495e;
            margin-top: 50px;
            border-bottom: 2px solid #bdc3c7;
            padding-bottom: 8px;
            font-size: 1.6em;
            page-break-before: auto;
        }
        h3 {
            color: #3498db;
            margin-top: 25px;
            font-size: 1.2em;
        }
        h4 {
            color: #7f8c8d;
            margin-top: 15px;
            font-size: 1em;
        }
        .circuit-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 25px;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        .circuit-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .family-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 0.9em;
            margin-right: 15px;
            color: white;
        }
        .family-S { background-color: #3498db; }
        .family-C { background-color: #27ae60; }
        .family-O { background-color: #e67e22; }
        .family-M { background-color: #9b59b6; }
        .circuit-title {
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
        }
        .qubit-count {
            background: #ecf0f1;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            margin-left: 10px;
            color: #7f8c8d;
        }
        .circuit-diagram {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .circuit-diagram img {
            max-width: 100%;
            height: auto;
        }
        .section {
            margin: 15px 0;
        }
        .section-title {
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', monospace;
        }
        .physics-box {
            background: #eef6f9;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
        }
        .importance-box {
            background: #fef9e7;
            border-left: 4px solid #f1c40f;
            padding: 15px;
            margin: 15px 0;
        }
        .toc {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 20px 30px;
            margin: 30px 0;
        }
        .toc ul {
            list-style: none;
            padding-left: 0;
        }
        .toc li {
            padding: 5px 0;
        }
        .toc a {
            color: #3498db;
            text-decoration: none;
        }
        .toc a:hover {
            text-decoration: underline;
        }
        .family-section {
            margin-top: 40px;
        }
        .intro-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
        }
        .intro-box h3 {
            color: white;
            margin-top: 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background: #3498db;
            color: white;
        }
        tr:nth-child(even) {
            background: #f9f9f9;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: center;
        }
    </style>
</head>
<body>

<h1>QuartumSE Benchmark Circuits</h1>
<p><strong>A Complete Guide to the 12 Quantum Circuits</strong></p>
<p style="color: #7f8c8d;">Generated: January 31, 2026 | QuartumSE Classical Shadows Framework</p>

<div class="intro-box">
    <h3>What This Document Covers</h3>
    <p>This guide explains the 12 quantum circuits used in the QuartumSE classical shadows benchmark suite.
    For each circuit, you'll learn:</p>
    <ul>
        <li><strong>What it is:</strong> The quantum state being prepared</li>
        <li><strong>How it works:</strong> The physics and mathematics behind it</li>
        <li><strong>Why it matters:</strong> Real-world applications and importance</li>
        <li><strong>Circuit diagram:</strong> Visual representation of the quantum gates</li>
    </ul>
</div>

<div class="toc">
    <h3>Table of Contents</h3>
    <ul>
        <li><strong>Shadows Core (S)</strong> - Fundamental entangled states
            <ul>
                <li><a href="#S-GHZ-4">S-GHZ-4: 4-Qubit GHZ State</a></li>
                <li><a href="#S-GHZ-5">S-GHZ-5: 5-Qubit GHZ State</a></li>
                <li><a href="#S-BELL-2">S-BELL-2: 2 Bell Pairs</a></li>
                <li><a href="#S-BELL-3">S-BELL-3: 3 Bell Pairs</a></li>
                <li><a href="#S-ISING-4">S-ISING-4: 4-Qubit Ising</a></li>
                <li><a href="#S-ISING-6">S-ISING-6: 6-Qubit Ising</a></li>
            </ul>
        </li>
        <li><strong>Chemistry (C)</strong> - Molecular ground states
            <ul>
                <li><a href="#C-H2">C-H2: Hydrogen Molecule</a></li>
                <li><a href="#C-LiH">C-LiH: Lithium Hydride</a></li>
            </ul>
        </li>
        <li><strong>Optimization (O)</strong> - QAOA circuits
            <ul>
                <li><a href="#O-QAOA-5">O-QAOA-5: 5-Node MAX-CUT</a></li>
                <li><a href="#O-QAOA-7">O-QAOA-7: 7-Node MAX-CUT</a></li>
            </ul>
        </li>
        <li><strong>Metrology (M)</strong> - Quantum sensing
            <ul>
                <li><a href="#M-PHASE-3">M-PHASE-3: 3-Qubit Phase Sensing</a></li>
                <li><a href="#M-PHASE-4">M-PHASE-4: 4-Qubit Phase Sensing</a></li>
            </ul>
        </li>
    </ul>
</div>

<h2>Overview: Circuit Families</h2>

<table>
    <tr>
        <th>Family</th>
        <th>Code</th>
        <th>Circuits</th>
        <th>Purpose</th>
    </tr>
    <tr>
        <td><strong>Shadows Core</strong></td>
        <td>S</td>
        <td>6</td>
        <td>Validate shadow estimation on fundamental entangled states</td>
    </tr>
    <tr>
        <td><strong>Chemistry</strong></td>
        <td>C</td>
        <td>2</td>
        <td>Molecular ground state energy estimation</td>
    </tr>
    <tr>
        <td><strong>Optimization</strong></td>
        <td>O</td>
        <td>2</td>
        <td>QAOA cost function estimation for combinatorial problems</td>
    </tr>
    <tr>
        <td><strong>Metrology</strong></td>
        <td>M</td>
        <td>2</td>
        <td>Quantum-enhanced parameter estimation</td>
    </tr>
</table>

"""]

    # Add each circuit
    current_family = None
    family_order = ["Shadows Core", "Chemistry", "Optimization", "Metrology"]

    for family_name in family_order:
        # Add family header
        family_circuits = [(cid, info) for cid, info in CIRCUITS.items() if info["family"] == family_name]
        if not family_circuits:
            continue

        family_code = family_circuits[0][1]["family_code"]
        html_parts.append(f"""
<div class="family-section">
<h2><span class="family-badge family-{family_code}">{family_code}</span> {family_name} Circuits</h2>
""")

        for circuit_id, info in family_circuits:
            img_data = circuit_images.get(circuit_id)
            img_html = f'<img src="data:image/png;base64,{img_data}" alt="{circuit_id} circuit diagram">' if img_data else '<p><em>Circuit diagram generation failed</em></p>'

            html_parts.append(f"""
<div class="circuit-card" id="{circuit_id}">
    <div class="circuit-header">
        <span class="family-badge family-{info['family_code']}">{circuit_id}</span>
        <span class="circuit-title">{info['name']}</span>
        <span class="qubit-count">{info['qubits']} qubits</span>
    </div>

    <p><em>{info['short_desc']}</em></p>

    <div class="circuit-diagram">
        {img_html}
    </div>

    <div class="section">
        <div class="section-title">Description</div>
        <p>{info['description'].strip()}</p>
    </div>

    <div class="physics-box">{info['physics'].strip()}</div>

    <div class="section">
        <div class="section-title">Applications</div>
        {info['applications'].strip()}
    </div>

    <div class="importance-box">
        <div class="section-title">Why This Circuit Matters for Benchmarking</div>
        <p>{info['importance'].strip()}</p>
    </div>
</div>
""")

        html_parts.append("</div>")  # Close family section

    # Add footer
    html_parts.append("""
<div class="footer">
    <p><strong>QuartumSE Classical Shadows Benchmark Suite</strong><br>
    This document accompanies the benchmark results from the overnight run of January 30-31, 2026.<br>
    <br>
    For questions or contributions, see the QuartumSE GitHub repository.</p>
</div>

</body>
</html>
""")

    # Write HTML file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    print(f"\nReport generated: {output_path}")


if __name__ == "__main__":
    output_path = Path(__file__).parent / "circuit_guide_complete.html"
    generate_html_report(output_path)
    print("Done!")
