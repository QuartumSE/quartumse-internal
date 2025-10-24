#!/usr/bin/env python3
"""Template CLI for running and caching Phase 1 reference simulations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml
from qiskit import QuantumCircuit

# Ensure the local ``quartumse`` package is importable when running from source
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from experiments.shadows.common_utils import run_shadows
from quartumse.shadows.core import Observable


DEFAULT_CONFIG: Dict[str, Any] = {
    "experiment_name": "ghz-reference",
    "phase": "phase1",
    "default_tags": ["phase1", "reference"],
    "runs": [
        {
            "name": "ghz-3q-baseline",
            "reference_slug": "phase1-ghz-v0-n3-s4096",
            "circuit": "ghz",
            "num_qubits": 3,
            "variant": "v0",
            "shadow_size": 4096,
            "backend": "aer_simulator",
            "tags": ["ghz"],
            "observables": ["ZII", "IZI", "IIZ", "ZZI", "ZZZ"],
        },
        {
            "name": "ghz-3q-mem",
            "reference_slug": "phase1-ghz-v1-n3-s4096",
            "circuit": "ghz",
            "num_qubits": 3,
            "variant": "v1",
            "shadow_size": 4096,
            "mem_shots": 512,
            "backend": "aer_simulator",
            "tags": ["ghz", "mem"],
            "observables": ["ZII", "IZI", "IIZ", "ZZI", "ZZZ"],
        },
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 1 reference simulations and reuse cached datasets",
    )
    parser.add_argument("--config", type=Path, help="Path to YAML/JSON configuration override")
    parser.add_argument("--backend", help="Override backend descriptor for all runs")
    parser.add_argument(
        "--variant",
        choices=["v0", "v1"],
        help="Override the classical shadows variant (per-run config still allowed)",
    )
    parser.add_argument(
        "--shadow-size",
        type=int,
        help="Override the number of measurement shots per run",
    )
    parser.add_argument(
        "--mem-shots",
        type=int,
        default=512,
        help="Default MEM shots per basis state when variant=v1",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory used for manifests and shot archives",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore cached reference datasets and regenerate measurements",
    )
    parser.add_argument(
        "--force-new-calibration",
        action="store_true",
        help="Force a fresh MEM calibration when variant=v1",
    )
    parser.add_argument(
        "--calibration-max-age-hours",
        type=float,
        default=None,
        help="Maximum age for reusing MEM calibrations (overrides config)",
    )
    return parser.parse_args()


def load_config(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return DEFAULT_CONFIG

    data = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(data)
    if not isinstance(loaded, dict):
        raise ValueError("Configuration file must contain a mapping at the top level")
    return loaded


def create_ghz_circuit(num_qubits: int) -> QuantumCircuit:
    qc = QuantumCircuit(num_qubits)
    qc.name = f"GHZ-{num_qubits}"
    qc.h(0)
    for idx in range(1, num_qubits):
        qc.cx(0, idx)
    return qc


def build_circuit(run_cfg: Dict[str, Any]) -> QuantumCircuit:
    circuit_type = (run_cfg.get("circuit") or "ghz").lower()
    num_qubits = int(run_cfg.get("num_qubits", 3))
    if circuit_type == "ghz":
        return create_ghz_circuit(num_qubits)
    raise ValueError(f"Unsupported circuit type for reference template: {circuit_type}")


def build_observables(config: Optional[Iterable[Any]], num_qubits: int) -> List[Observable]:
    if not config:
        return default_ghz_observables(num_qubits)

    observables: List[Observable] = []
    for entry in config:
        if isinstance(entry, str):
            pauli = entry
            coefficient = 1.0
        elif isinstance(entry, dict):
            pauli = entry.get("pauli") or entry.get("operator")
            coefficient = entry.get("coefficient", 1.0)
        else:
            raise TypeError(f"Unsupported observable specification: {entry!r}")
        if not isinstance(pauli, str):
            raise TypeError(f"Observable pauli string must be str, got {type(pauli)}")
        if len(pauli) != num_qubits:
            raise ValueError(
                f"Observable '{pauli}' must match circuit width ({num_qubits} qubits)",
            )
        observables.append(Observable(pauli, coefficient=float(coefficient)))
    return observables


def default_ghz_observables(num_qubits: int) -> List[Observable]:
    base = []
    for qubit in range(num_qubits):
        pauli = "I" * qubit + "Z" + "I" * (num_qubits - qubit - 1)
        base.append(Observable(pauli, coefficient=1.0))
    if num_qubits >= 2:
        pauli = "Z" + "Z" + "I" * (num_qubits - 2)
        base.append(Observable(pauli, coefficient=1.0))
    pauli_all = "Z" * num_qubits
    base.append(Observable(pauli_all, coefficient=1.0))
    return base


def merge_tags(*collections: Optional[Iterable[str]]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for collection in collections:
        if not collection:
            continue
        for tag in collection:
            if tag not in seen:
                seen.add(tag)
                ordered.append(tag)
    return ordered


def derive_slug(run_cfg: Dict[str, Any], fallback_phase: str) -> str:
    slug = run_cfg.get("reference_slug")
    if slug:
        return str(slug)

    circuit = (run_cfg.get("circuit") or "circuit").lower()
    variant = (run_cfg.get("variant") or "v0").lower()
    num_qubits = int(run_cfg.get("num_qubits", 0))
    shots = int(run_cfg.get("shadow_size", 0))
    return f"{fallback_phase}-{circuit}-{variant}-n{num_qubits}-s{shots}"


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    data_dir = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    runs = config.get("runs") or []
    if not runs:
        print("No reference runs defined in configuration", file=sys.stderr)
        return 1

    default_tags = config.get("default_tags", [])
    experiment_name = config.get("experiment_name", "phase1-reference")
    phase = config.get("phase", "phase1")

    for run_cfg in runs:
        run_name = run_cfg.get("name") or run_cfg.get("reference_slug")
        slug = derive_slug(run_cfg, phase)
        backend_descriptor = args.backend or run_cfg.get("backend", "aer_simulator")
        variant = args.variant or run_cfg.get("variant", "v0")
        shadow_size = args.shadow_size or int(run_cfg.get("shadow_size", 4096))
        mem_shots = int(run_cfg.get("mem_shots", args.mem_shots))
        calibration_max_age = (
            args.calibration_max_age_hours
            if args.calibration_max_age_hours is not None
            else run_cfg.get("calibration_max_age_hours")
        )

        circuit = build_circuit(run_cfg)
        circuit.name = run_name or circuit.name
        observables = build_observables(run_cfg.get("observables"), circuit.num_qubits)

        tags = merge_tags(default_tags, run_cfg.get("tags"), [phase])
        metadata = {
            "experiment": experiment_name,
            "phase": phase,
            "run_name": run_name or slug,
        }
        metadata.update(run_cfg.get("metadata", {}))

        print("\n" + "=" * 80)
        print(f"Reference run: {run_name or slug}")
        print("=" * 80)
        print(f"Slug: {slug}")
        print(f"Backend: {backend_descriptor}")
        print(f"Variant: {variant.upper()}")
        print(f"Shadow size: {shadow_size}")
        if variant.lower() == "v1":
            print(f"MEM shots per basis: {mem_shots}")
        print(f"Circuit: {circuit.name} ({circuit.num_qubits} qubits)")
        print(f"Observables: {', '.join(str(obs) for obs in observables)}")

        results, meta = run_shadows(
            circuit,
            observables,
            backend_descriptor=backend_descriptor,
            variant=variant,
            shadow_size=shadow_size,
            mem_shots=mem_shots,
            data_dir=str(data_dir),
            reference_slug=slug,
            reference_tags=tags,
            reference_metadata=metadata,
            allow_reuse=not args.force,
            calibration_max_age_hours=calibration_max_age,
            force_new_calibration=args.force_new_calibration,
        )

        status = "reused" if meta.get("reference_reused") else "generated"
        print(f"Status: {status.upper()}")
        print(f"Manifest: {meta.get('manifest_path')}")
        print(f"Shot data: {meta.get('shot_data_path')}")
        print(f"Total shots: {meta.get('total_shots')}")

        print("\nObservables summary:")
        for obs, payload in results.items():
            expectation = payload.get("expectation")
            ci = payload.get("ci")
            ci_width = payload.get("ci_width")
            ci_str = "N/A" if ci is None else f"[{ci[0]:.4f}, {ci[1]:.4f}]"
            width_str = "N/A" if ci_width is None else f"±{ci_width:.4f}"
            print(f"  {obs:<10} -> {expectation:>8.4f}  CI: {ci_str}  Width: {width_str}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
