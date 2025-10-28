"""Command-line entrypoint orchestrating the full Phase-1 pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping

import yaml

from .analyzer import analyze_experiment
from .executor import execute_experiment
from .metadata_schema import ExperimentMetadata
from .reporter import generate_report
from .verifier import verify_experiment


def _load_metadata(path: Path) -> ExperimentMetadata:
    """Load experiment metadata from a YAML or JSON file."""

    raw_text = path.read_text(encoding="utf-8")
    data: Dict[str, Any]
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw_text) or {}
    else:
        data = json.loads(raw_text)
    return ExperimentMetadata.model_validate(data)


def _normalise_targets(metadata: ExperimentMetadata) -> Dict[str, float]:
    """Derive numeric metric targets from metadata."""

    targets: Dict[str, float] = {}

    if metadata.targets:
        for key, value in metadata.targets.items():
            try:
                targets[key] = float(value)
            except (TypeError, ValueError):
                continue

    if targets:
        return targets

    for entry in metadata.success_criteria:
        lowered = entry.lower()
        numbers = []
        for token in lowered.replace("%", " %").split():
            try:
                numbers.append(float(token.strip("%")))
            except ValueError:
                continue

        if "ssr" in lowered and numbers:
            targets.setdefault("ssr_average", numbers[0])
        if "ci" in lowered and "coverage" in lowered and numbers:
            value = numbers[0]
            if "%" in entry:
                value /= 100.0
            targets.setdefault("ci_coverage", value)

    return targets


def _prepare_artifacts(result: Mapping[str, Path], digest: str) -> Dict[str, Any]:
    """Create an artifacts payload for reporting."""

    return {
        "result_hash": digest,
        "manifests": {
            "baseline": str(result["manifest_baseline"]),
            "v0": str(result["manifest_v0"]),
            "v1": str(result["manifest_v1"]),
        },
        "raw_outputs": {key: str(path) for key, path in result.items()},
    }


def _format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _evaluate_targets(summary: Mapping[str, Any], targets: Mapping[str, float]) -> Dict[str, bool]:
    """Return a map indicating whether metrics meet their targets."""

    results: Dict[str, bool] = {}
    for metric, threshold in targets.items():
        actual = summary.get(metric)
        if actual is None:
            results[metric] = False
            continue
        try:
            value = float(actual)
        except (TypeError, ValueError):
            results[metric] = False
            continue
        results[metric] = value >= threshold
    return results


def _write_json(path: Path, payload: MutableMapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_pipeline(metadata_path: Path, output_dir: Path, backend: str | None = None) -> int:
    """Execute, verify, analyse, and report on an experiment."""

    metadata = _load_metadata(metadata_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    execution_result = execute_experiment(metadata, output_dir=output_dir, backend=backend)

    digest = execution_result["result_hash"].read_text(encoding="utf-8").strip()

    verification = verify_experiment(execution_result["manifest_v1"])
    verification_errors = verification.get("errors") or []

    manifest_v0 = json.loads(execution_result["manifest_v0"].read_text(encoding="utf-8"))
    manifest_v1 = json.loads(execution_result["manifest_v1"].read_text(encoding="utf-8"))
    manifest_baseline = json.loads(
        execution_result["manifest_baseline"].read_text(encoding="utf-8")
    )

    targets = _normalise_targets(metadata)
    analysis = analyze_experiment(
        manifest_v0,
        manifest_v1,
        manifest_baseline,
        ground_truth=metadata.ground_truth,
        targets=targets if targets else None,
    )

    summary_metrics = analysis.get("summary_metrics", {})
    analysis_targets = analysis.get("targets", targets)
    target_results = _evaluate_targets(summary_metrics, analysis_targets)

    analysis_path = output_dir / f"analysis_{digest}.json"
    _write_json(analysis_path, dict(analysis))

    artifacts = _prepare_artifacts(execution_result, digest)
    report_path = output_dir / f"report_{digest}.html"
    generate_report(metadata, artifacts, analysis, verification, report_path)

    print(f"Result hash: {digest}")
    print(f"Report: {report_path}")
    for metric in ("ssr_average", "ci_coverage"):
        if metric in summary_metrics:
            print(f"{metric}: {_format_metric(summary_metrics.get(metric))}")

    exit_code = 0
    if verification_errors:
        print("Verification issues detected:")
        for error in verification_errors:
            print(f" - {error}")
        exit_code = 1

    if target_results:
        unmet = [metric for metric, passed in target_results.items() if not passed]
        if unmet:
            print("Targets not met:")
            for metric in unmet:
                threshold = analysis_targets.get(metric)
                actual = summary_metrics.get(metric)
                print(f" - {metric}: {_format_metric(actual)} (target ≥ {threshold})")
            exit_code = 2

    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the full QuartumSE experiment pipeline")
    parser.add_argument("--metadata", required=True, type=Path, help="Path to metadata file")
    parser.add_argument(
        "--backend",
        type=str,
        default=None,
        help="Backend identifier to override metadata device",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Directory for generated artifacts",
    )

    args = parser.parse_args(argv)
    return run_pipeline(args.metadata, args.output, backend=args.backend)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())


__all__ = ["run_pipeline", "main"]
