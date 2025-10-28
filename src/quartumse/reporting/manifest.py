"""
Provenance Manifest - Complete experimental lineage tracking.

The manifest captures every detail needed to reproduce a quantum experiment:
- Circuit fingerprints and transpilation metadata
- Backend calibration snapshots
- Mitigation configurations
- Shot data locations
- Cost and resource usage
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)


class CircuitFingerprint(BaseModel):
    """Unique identifier for a quantum circuit."""

    qasm3: str = Field(description="OpenQASM 3.0 representation")
    num_qubits: int
    depth: int
    gate_counts: Dict[str, int] = Field(default_factory=dict)
    circuit_hash: Optional[str] = Field(default=None, description="SHA256 hash of QASM")

    @field_validator("circuit_hash", mode="before")
    @classmethod
    def compute_hash(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Compute SHA256 hash if not provided."""
        if v is None:
            qasm = info.data.get("qasm3", "")
            return hashlib.sha256(qasm.encode()).hexdigest()[:16]
        return v

    @model_validator(mode="after")
    def ensure_hash(self) -> "CircuitFingerprint":
        """Ensure a circuit hash is populated even if validator shortcuts."""

        if self.circuit_hash is None:
            self.circuit_hash = hashlib.sha256(self.qasm3.encode()).hexdigest()[:16]
        return self


class BackendSnapshot(BaseModel):
    """Snapshot of backend calibration at experiment time."""

    backend_name: str
    backend_version: str
    num_qubits: int
    coupling_map: Optional[List[List[int]]] = None
    basis_gates: List[str]

    # Calibration data
    t1_times: Optional[Dict[int, float]] = Field(None, description="T1 times (us) per qubit")
    t2_times: Optional[Dict[int, float]] = Field(None, description="T2 times (us) per qubit")
    gate_errors: Optional[Dict[str, float]] = Field(None, description="Gate errors by gate type")
    readout_errors: Optional[Dict[int, float]] = Field(None, description="Readout errors per qubit")

    calibration_timestamp: datetime
    properties_hash: str = Field(description="Hash of full properties JSON")


def compute_file_checksum(
    path: Union[str, Path],
    *,
    algorithm: str = "sha256",
    chunk_size: int = 64 * 1024,
) -> Optional[str]:
    """Compute a checksum for ``path`` using ``algorithm``.

    Args:
        path: File path to hash.
        algorithm: Hash algorithm to use (default: ``sha256``).
        chunk_size: Chunk size used when streaming the file.

    Returns:
        Hex digest string if the file exists, otherwise ``None``.
    """

    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None

    digest = hashlib.new(algorithm)
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MitigationConfig(BaseModel):
    """Error mitigation techniques applied."""

    techniques: List[str] = Field(
        default_factory=list, description="e.g., ['MEM', 'ZNE', 'RC']"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Technique-specific parameters"
    )

    # For MEM
    confusion_matrix_path: Optional[str] = None
    confusion_matrix_checksum: Optional[str] = Field(
        default=None, description="Checksum of the MEM confusion matrix file"
    )

    # For ZNE
    zne_scale_factors: Optional[List[float]] = None
    zne_extrapolator: Optional[str] = None

    # For randomized compiling
    rc_num_samples: Optional[int] = None


class ShadowsConfig(BaseModel):
    """Classical shadows configuration."""

    version: str = Field(description="v0, v1, v2, v3, v4")
    shadow_size: int = Field(description="Number of random measurements")
    measurement_ensemble: str = Field(
        default="random_local_clifford", description="Ensemble type"
    )

    # v1+ (noise-aware)
    noise_model_path: Optional[str] = None
    inverse_channel_applied: bool = False

    # v2+ (fermionic)
    fermionic_mode: bool = False
    rdm_order: Optional[int] = Field(None, description="Reduced density matrix order (1 or 2)")

    # v3+ (adaptive)
    adaptive: bool = False
    target_observables: Optional[List[str]] = Field(None, description="Observable prioritization")

    # v4+ (robust Bayesian)
    bayesian_inference: bool = False
    bootstrap_samples: Optional[int] = None


class ResourceUsage(BaseModel):
    """Resource consumption tracking."""

    total_shots: int
    execution_time_seconds: float
    queue_time_seconds: Optional[float] = None

    # Cost tracking
    estimated_cost_usd: Optional[float] = Field(None, description="Estimated dollar cost")
    credits_used: Optional[float] = Field(None, description="Backend-specific credits")

    # Compute resources
    classical_compute_seconds: Optional[float] = Field(
        None, description="Post-processing time"
    )


class ManifestSchema(BaseModel):
    """
    Complete provenance manifest for a quantum experiment.

    This is the authoritative record of what was run, where, when, and how.
    """

    # Metadata
    manifest_version: str = Field(default="1.0.0", description="Manifest schema version")
    experiment_id: str = Field(description="Unique experiment identifier (UUID)")
    experiment_name: Optional[str] = Field(None, description="Human-readable name")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Experiment definition
    circuit: CircuitFingerprint
    observables: List[Dict[str, Any]] = Field(
        description="Observables estimated (Pauli strings, etc.)"
    )

    # Execution context
    backend: BackendSnapshot
    mitigation: MitigationConfig = Field(default_factory=MitigationConfig)
    shadows: Optional[ShadowsConfig] = None

    # Results & data
    shot_data_path: str = Field(description="Path to Parquet file with shot results")
    shot_data_checksum: Optional[str] = Field(
        default=None, description="Checksum of the shot data file"
    )
    results_summary: Dict[str, Any] = Field(
        description="High-level results (expectation values, CIs, etc.)"
    )
    resource_usage: ResourceUsage

    # Reproducibility
    random_seed: Optional[int] = None
    quartumse_version: str
    qiskit_version: str
    python_version: str

    # Extensions
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="User-defined metadata"
    )
    tags: List[str] = Field(default_factory=list, description="Searchable tags")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class ProvenanceManifest:
    """
    High-level interface for creating and managing provenance manifests.
    """

    def __init__(self, schema: ManifestSchema):
        self.schema = schema

    @classmethod
    def create(
        cls,
        experiment_id: str,
        circuit_fingerprint: CircuitFingerprint,
        backend_snapshot: BackendSnapshot,
        **kwargs: Any,
    ) -> "ProvenanceManifest":
        """Create a new manifest with required fields."""
        schema = ManifestSchema(
            experiment_id=experiment_id,
            circuit=circuit_fingerprint,
            backend=backend_snapshot,
            **kwargs,
        )
        return cls(schema)

    def to_json(self, path: Optional[Union[str, Path]] = None) -> str:
        """Export manifest as JSON."""
        json_str = self.schema.model_dump_json(indent=2)

        if path:
            Path(path).write_text(json_str)

        return json_str

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "ProvenanceManifest":
        """Load manifest from JSON file."""
        json_data = Path(path).read_text()
        schema = ManifestSchema.model_validate_json(json_data)
        return cls(schema)

    def add_tag(self, tag: str) -> None:
        """Add a searchable tag."""
        if tag not in self.schema.tags:
            self.schema.tags.append(tag)

    def update_results(self, results: Dict[str, Any]) -> None:
        """Update the results summary."""
        self.schema.results_summary.update(results)

    def validate(self, *, require_shot_file: bool = True) -> bool:
        """Validate the manifest schema and ensure referenced artifacts exist."""

        if require_shot_file:
            shot_path = Path(self.schema.shot_data_path)
            if not shot_path.exists():
                raise FileNotFoundError(
                    f"Shot data referenced by manifest is missing: {shot_path}"
                )

        return True

    def __repr__(self) -> str:
        return (
            f"ProvenanceManifest(id={self.schema.experiment_id}, "
            f"backend={self.schema.backend.backend_name}, "
            f"created={self.schema.created_at.isoformat()})"
        )
