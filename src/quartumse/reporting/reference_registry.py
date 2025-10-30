"""Utilities for tracking and reusing reference experiment datasets."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from quartumse.reporting.manifest import ProvenanceManifest


class ReferenceDatasetRegistry:
    """Persisted lookup table for reference manifests and associated metadata."""

    def __init__(self, base_dir: str | Path = "data") -> None:
        self.base_dir = Path(base_dir)
        self.manifests_dir = self.base_dir / "manifests"
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.manifests_dir / "reference_index.json"

    # ------------------------------------------------------------------
    # Index management helpers
    # ------------------------------------------------------------------
    def _load_index(self) -> dict[str, str]:
        if not self.index_path.exists():
            return {}
        try:
            with self.index_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass
        return {}

    def _save_index(self, index: dict[str, str]) -> None:
        with self.index_path.open("w", encoding="utf-8") as handle:
            json.dump(index, handle, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def lookup(self, slug: str) -> Path | None:
        """Return the manifest path associated with ``slug`` if it exists."""

        index = self._load_index()
        path_str = index.get(slug)
        if path_str:
            manifest_path = Path(path_str)
            if manifest_path.exists():
                return manifest_path
            # Remove stale entry
            index.pop(slug, None)
            self._save_index(index)

        scanned_path = self._scan_manifests_for_slug(slug)
        if scanned_path:
            index[slug] = str(scanned_path.resolve())
            self._save_index(index)
            return scanned_path

        return None

    def register_reference(
        self,
        slug: str,
        manifest_path: str | Path,
        *,
        tags: Iterable[str] | None = None,
        metadata: dict[str, str | int | float | bool | None] | None = None,
        calibration_shots: int = 0,
    ) -> ProvenanceManifest:
        """Attach metadata to a manifest and register it under ``slug``."""

        manifest_path = Path(manifest_path)
        manifest = ProvenanceManifest.from_json(manifest_path)

        dataset_meta = dict(manifest.schema.metadata.get("reference_dataset", {}))
        now = datetime.utcnow().isoformat()
        dataset_meta.update(metadata or {})
        dataset_meta.update(
            {
                "slug": slug,
                "calibration_shots": int(calibration_shots),
                "registered_at": dataset_meta.get("registered_at") or now,
                "last_used_at": now,
                "shot_data_path": manifest.schema.shot_data_path,
            }
        )

        dataset_tags: list[str] = list(dataset_meta.get("tags", []))
        if tags:
            for tag in tags:
                if tag not in dataset_tags:
                    dataset_tags.append(tag)
        dataset_meta["tags"] = dataset_tags

        manifest.schema.metadata["reference_dataset"] = dataset_meta

        manifest_tags: list[str] = list(manifest.schema.tags or [])
        manifest_tags.append("reference-dataset")
        if tags:
            for tag in tags:
                if tag not in manifest_tags:
                    manifest_tags.append(tag)
        manifest.schema.tags = sorted(set(manifest_tags))

        manifest.to_json(manifest_path)

        index = self._load_index()
        index[slug] = str(manifest_path.resolve())
        self._save_index(index)

        return manifest

    def mark_used(self, slug: str, manifest_path: str | Path | None = None) -> None:
        """Update ``last_used_at`` for the manifest associated with ``slug``."""

        resolved_path: Path | None
        if manifest_path is None:
            resolved_path = self.lookup(slug)
        else:
            resolved_path = Path(manifest_path)

        if resolved_path is None:
            return

        manifest = ProvenanceManifest.from_json(resolved_path)
        dataset_meta = dict(manifest.schema.metadata.get("reference_dataset", {}))
        dataset_meta.setdefault("slug", slug)
        dataset_meta["last_used_at"] = datetime.utcnow().isoformat()
        manifest.schema.metadata["reference_dataset"] = dataset_meta
        manifest.to_json(resolved_path)

    def load_manifest(self, manifest_path: str | Path) -> ProvenanceManifest:
        """Load a manifest from disk."""

        return ProvenanceManifest.from_json(Path(manifest_path))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _scan_manifests_for_slug(self, slug: str) -> Path | None:
        for manifest_path in sorted(self.manifests_dir.glob("*.json")):
            try:
                manifest = ProvenanceManifest.from_json(manifest_path)
            except Exception:
                continue
            metadata = manifest.schema.metadata.get("reference_dataset")
            if isinstance(metadata, dict) and metadata.get("slug") == slug:
                return manifest_path
        return None
