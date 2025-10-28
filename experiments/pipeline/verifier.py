"""Stage-2 verifier utilities for provenance manifests."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any, Dict, Optional

import qiskit
from qiskit_aer import AerSimulator

from quartumse import __version__ as QUARTUMSE_VERSION
from quartumse.estimator import ShadowEstimator
from quartumse.reporting.manifest import (
    MitigationConfig,
    ProvenanceManifest,
    compute_file_checksum,
)
from quartumse.shadows import ShadowConfig


def _resolve_artifact_path(
    artifact: Optional[str],
    manifest_path: Path,
    *,
    data_dir: Optional[Path] = None,
    mem_subdir: bool = False,
) -> Optional[Path]:
    """Resolve an artifact path referenced in the manifest."""

    if not artifact:
        return None

    raw_path = Path(artifact)
    candidates = [raw_path]

    if not raw_path.is_absolute():
        candidates.append((manifest_path.parent / raw_path).resolve())
        if data_dir is not None:
            candidates.append((data_dir / raw_path).resolve())

    if data_dir is not None and mem_subdir:
        candidates.append((data_dir / "mem" / raw_path.name).resolve())
    if mem_subdir:
        candidates.append((manifest_path.parent / "mem" / raw_path.name).resolve())

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return raw_path if raw_path.exists() else None


def _shadow_config_from_manifest(manifest: ProvenanceManifest) -> ShadowConfig:
    """Construct a :class:`ShadowConfig` from manifest shadows metadata."""

    shadows = manifest.schema.shadows
    payload: Dict[str, Any] = {}

    if shadows is not None:
        payload = {
            "version": shadows.version,
            "shadow_size": shadows.shadow_size,
            "measurement_ensemble": shadows.measurement_ensemble,
            "apply_inverse_channel": shadows.inverse_channel_applied,
            "noise_model_path": shadows.noise_model_path,
            "fermionic_mode": shadows.fermionic_mode,
            "rdm_order": shadows.rdm_order,
            "adaptive": shadows.adaptive,
            "target_observables": shadows.target_observables,
            "bayesian_inference": shadows.bayesian_inference,
            "bootstrap_samples": shadows.bootstrap_samples,
            "random_seed": manifest.schema.random_seed,
        }

    return ShadowConfig.model_validate(payload)


def _mitigation_config_from_manifest(manifest: ProvenanceManifest) -> MitigationConfig:
    """Return a mitigation configuration for estimator replay."""

    mitigation = manifest.schema.mitigation
    # Ensure we return a standalone object so tests can mutate manifests safely.
    return MitigationConfig.model_validate(mitigation.model_dump())


def _extract_expectations(results_summary: Dict[str, Any]) -> Dict[str, float]:
    """Extract expectation values from manifest results summary."""

    expectations: Dict[str, float] = {}
    for key, value in results_summary.items():
        if isinstance(value, dict) and "expectation_value" in value:
            expectations[key] = float(value["expectation_value"])
    return expectations


def verify_experiment(manifest_path: Path) -> Dict[str, Any]:
    """Verify manifest reproducibility and artifact integrity."""

    manifest_path = Path(manifest_path)

    verification: Dict[str, Any] = {
        "manifest_path": str(manifest_path),
        "manifest_exists": manifest_path.exists(),
        "manifest_valid": False,
        "shot_data_exists": False,
        "shot_data_path": None,
        "shot_data_checksum_matches": None,
        "mem_confusion_matrix_exists": None,
        "mem_confusion_matrix_path": None,
        "mem_confusion_matrix_checksum_matches": None,
        "replay_matches": False,
        "max_abs_diff": None,
        "software_versions": {
            "quartumse": QUARTUMSE_VERSION,
            "qiskit": qiskit.__version__,
            "python": platform.python_version(),
        },
        "errors": [],
    }

    if not verification["manifest_exists"]:
        verification["errors"].append(f"Manifest not found: {manifest_path}")
        return verification

    try:
        manifest = ProvenanceManifest.from_json(manifest_path)
        verification["manifest_valid"] = True
    except Exception as exc:  # pragma: no cover - defensive
        verification["errors"].append(f"Failed to load manifest: {exc}")
        return verification

    verification["software_versions"] = {
        "quartumse": manifest.schema.quartumse_version,
        "qiskit": manifest.schema.qiskit_version,
        "python": manifest.schema.python_version,
    }

    raw_shot_path = manifest.schema.shot_data_path
    data_dir: Optional[Path] = None

    resolved_shot_path = _resolve_artifact_path(raw_shot_path, manifest_path)
    if resolved_shot_path and resolved_shot_path.exists():
        verification["shot_data_exists"] = True
        verification["shot_data_path"] = str(resolved_shot_path)
        if resolved_shot_path.parent.name == "shots":
            data_dir = resolved_shot_path.parent.parent
        else:
            data_dir = resolved_shot_path.parent
        recorded_checksum = manifest.schema.shot_data_checksum
        if recorded_checksum:
            actual_checksum = compute_file_checksum(resolved_shot_path)
            matches = actual_checksum == recorded_checksum
            verification["shot_data_checksum_matches"] = matches
            if not matches:
                verification["errors"].append(
                    "Shot data checksum mismatch detected"
                )
    else:
        verification["errors"].append(
            f"Shot data referenced by manifest is missing: {raw_shot_path}"
        )
        verification["shot_data_path"] = str(resolved_shot_path) if resolved_shot_path else raw_shot_path
        if manifest.schema.shot_data_checksum:
            verification["shot_data_checksum_matches"] = False

    confusion_matrix_path = manifest.schema.mitigation.confusion_matrix_path
    resolved_confusion = _resolve_artifact_path(
        confusion_matrix_path,
        manifest_path,
        data_dir=data_dir,
        mem_subdir=True,
    )

    if confusion_matrix_path:
        exists = bool(resolved_confusion and Path(resolved_confusion).exists())
        verification["mem_confusion_matrix_exists"] = exists
        verification["mem_confusion_matrix_path"] = (
            str(resolved_confusion) if resolved_confusion else confusion_matrix_path
        )
        if not exists:
            verification["errors"].append(
                "Measurement error mitigation confusion matrix referenced in manifest "
                f"is missing: {confusion_matrix_path}"
            )
            if manifest.schema.mitigation.confusion_matrix_checksum:
                verification["mem_confusion_matrix_checksum_matches"] = False
        else:
            recorded_conf_checksum = manifest.schema.mitigation.confusion_matrix_checksum
            if recorded_conf_checksum:
                actual_conf_checksum = compute_file_checksum(resolved_confusion)
                matches = actual_conf_checksum == recorded_conf_checksum
                verification["mem_confusion_matrix_checksum_matches"] = matches
                if not matches:
                    verification["errors"].append(
                        "MEM confusion matrix checksum mismatch detected"
                    )

    if not verification["shot_data_exists"]:
        return verification

    if manifest.schema.shadows is None:
        verification["errors"].append(
            "Manifest does not contain classical shadows configuration; cannot replay."
        )
        return verification

    expectations = _extract_expectations(manifest.schema.results_summary)
    if not expectations:
        verification["errors"].append(
            "Manifest results summary does not include expectation values for replay."
        )
        return verification

    try:
        estimator = ShadowEstimator(
            backend=AerSimulator(),
            shadow_config=_shadow_config_from_manifest(manifest),
            mitigation_config=_mitigation_config_from_manifest(manifest),
            data_dir=data_dir or manifest_path.parent,
        )
        replay_result = estimator.replay_from_manifest(manifest_path)
    except Exception as exc:  # pragma: no cover - defensive
        verification["errors"].append(f"Replay from manifest failed: {exc}")
        return verification

    replay_expectations = _extract_expectations(replay_result.observables)

    missing_keys = set(expectations) ^ set(replay_expectations)
    if missing_keys:
        verification["errors"].append(
            "Mismatch in observable keys between manifest and replay: "
            + ", ".join(sorted(missing_keys))
        )
        return verification

    max_diff = max(
        abs(expectations[key] - replay_expectations[key]) for key in expectations
    )
    verification["max_abs_diff"] = max_diff

    if max_diff < 1e-12:
        verification["replay_matches"] = True
    else:
        verification["errors"].append(
            "Replay expectation values differ from manifest beyond tolerance"
        )

    return verification

