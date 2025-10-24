"""Measurement Error Mitigation (MEM) utilities."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Sequence, Tuple, Union

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.providers import Backend

from quartumse.connectors import create_runtime_sampler, is_ibm_runtime_backend


LOGGER = logging.getLogger(__name__)

__all__ = [
    "MeasurementErrorMitigation",
    "ReadoutCalibrationManager",
    "CalibrationRecord",
]


class MeasurementErrorMitigation:
    """
    Measurement error mitigation using confusion matrix inversion.

    Calibrates a confusion matrix and applies it to correct noisy measurements.
    """

    def __init__(self, backend: Backend):
        self.backend = backend
        self.confusion_matrix: Optional[np.ndarray] = None
        self._calibrated_qubits: Optional[tuple[int, ...]] = None
        self._runtime_sampler = None
        self._runtime_sampler_checked = False
        self._use_runtime_sampler = is_ibm_runtime_backend(backend)
        self.confusion_matrix_path: Optional[Path] = None
        self._confusion_metadata: Dict[str, Any] = {}

    def _get_runtime_sampler(self):
        """Initialise (if necessary) and return an IBM Runtime sampler."""

        if not self._use_runtime_sampler:
            return None

        if not self._runtime_sampler_checked:
            self._runtime_sampler = create_runtime_sampler(self.backend)
            self._runtime_sampler_checked = True

        return self._runtime_sampler

    def calibrate(
        self,
        qubits: Sequence[int],
        shots: int = 4096,
        run_options: Optional[Dict[str, object]] = None,
        *,
        output_path: Optional[Union[str, Path]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """
        Calibrate confusion matrix by preparing and measuring basis states.

        Args:
            qubits: List of qubit indices to calibrate
            shots: Number of calibration shots per basis state
            run_options: Backend execution options
            output_path: Optional path where the confusion matrix should be
                persisted. If provided the directory is created automatically
                and the matrix is saved as a compressed ``.npz`` archive.

        Returns:
            Path to the persisted confusion matrix if ``output_path`` is provided.
            The calibrated confusion matrix is stored on the instance as
            :attr:`confusion_matrix`.
        """

        if not qubits:
            raise ValueError("At least one qubit must be provided for calibration")

        run_options = dict(run_options or {})

        num_qubits = len(qubits)
        num_states = 2**num_qubits

        calibration_circuits: list[QuantumCircuit] = []
        for prepared_index in range(num_states):
            qc = QuantumCircuit(num_qubits, num_qubits)

            for qubit_idx in range(num_qubits):
                if (prepared_index >> qubit_idx) & 1:
                    qc.x(qubit_idx)

            qc.measure(range(num_qubits), range(num_qubits))
            calibration_circuits.append(qc)

        transpiled_circuits = transpile(
            calibration_circuits,
            backend=self.backend,
            initial_layout=list(qubits),
        )

        sampler = self._get_runtime_sampler()
        if sampler is not None:
            try:
                job = sampler.run(list(transpiled_circuits), shots=shots, **run_options)
            except TypeError:
                if run_options:
                    LOGGER.warning(
                        "SamplerV2.run does not accept run options %s; submitting without them.",
                        run_options,
                    )
                job = sampler.run(list(transpiled_circuits), shots=shots)
            result = job.result()

            def _get_counts(batch_index: int):
                pub_result = result[batch_index]
                data_bin = pub_result.data

                # SamplerV2 DataBin: try common measurement key names
                for key in ['meas', 'c', 'measure']:
                    if hasattr(data_bin, key):
                        return getattr(data_bin, key).get_counts()

                # Fallback: get first measurement attribute
                data_attrs = [attr for attr in dir(data_bin) if not attr.startswith('_')]
                if data_attrs:
                    return getattr(data_bin, data_attrs[0]).get_counts()

                raise AttributeError(f"Could not find measurement data in DataBin. Available attributes: {data_attrs}")

        else:
            job = self.backend.run(transpiled_circuits, shots=shots, **run_options)
            result = job.result()

            def _get_counts(batch_index: int):
                return result.get_counts(batch_index)

        confusion = np.zeros((num_states, num_states), dtype=float)
        for prepared_index in range(num_states):
            counts = _get_counts(prepared_index)
            total = sum(counts.values())
            if total == 0:
                continue

            for bitstring, count in counts.items():
                measured_index = self._bitstring_to_index(bitstring)
                confusion[measured_index, prepared_index] = count / total

        self.confusion_matrix = confusion
        self._calibrated_qubits = tuple(qubits)

        if metadata is None:
            metadata = {
                "created_at": datetime.utcnow().isoformat(),
                "qubits": list(qubits),
                "shots_per_state": shots,
                "total_shots": shots * num_states,
            }
        else:
            metadata = metadata.copy()
            metadata.setdefault("created_at", datetime.utcnow().isoformat())
            metadata.setdefault("qubits", list(qubits))
            metadata.setdefault("shots_per_state", shots)
            metadata.setdefault("total_shots", shots * num_states)

        self._confusion_metadata = metadata

        self.confusion_matrix_path = None
        if output_path is not None:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            metadata_json = json.dumps(metadata)
            np.savez_compressed(path, confusion_matrix=confusion, metadata=np.array(metadata_json))
            self.confusion_matrix_path = path.resolve()

        return self.confusion_matrix_path

    def load_confusion_matrix(self, path: Union[str, Path]) -> np.ndarray:
        """Load a persisted confusion matrix archive."""

        archive_path = Path(path)
        if not archive_path.exists():
            raise FileNotFoundError(f"Confusion matrix archive not found: {archive_path}")

        confusion, metadata = self._read_confusion_archive(archive_path)
        self.confusion_matrix = confusion
        self.confusion_matrix_path = archive_path.resolve()
        self._confusion_metadata = metadata

        qubit_meta = metadata.get("qubits") if isinstance(metadata, dict) else None
        if isinstance(qubit_meta, (list, tuple)):
            try:
                self._calibrated_qubits = tuple(int(q) for q in qubit_meta)
            except (TypeError, ValueError):
                LOGGER.warning("Unable to parse calibrated qubits metadata from %s", archive_path)
                self._calibrated_qubits = None

        return confusion

    def get_confusion_metadata(self) -> Dict[str, Any]:
        """Return metadata captured during calibration."""

        return self._confusion_metadata.copy()

    @staticmethod
    def _read_confusion_archive(path: Union[str, Path]) -> tuple[np.ndarray, Dict[str, Any]]:
        archive_path = Path(path)
        with np.load(archive_path, allow_pickle=False) as archive:
            confusion = np.asarray(archive["confusion_matrix"], dtype=float)
            metadata: Dict[str, Any] = {}
            if "metadata" in archive:
                raw_metadata = archive["metadata"]
                if isinstance(raw_metadata, np.ndarray):
                    if raw_metadata.ndim == 0:
                        metadata_json = str(raw_metadata.item())
                    else:
                        metadata_json = json.dumps(raw_metadata.tolist())
                else:
                    metadata_json = str(raw_metadata)

                metadata_json = metadata_json.strip()
                if metadata_json and metadata_json not in {"None", "nan"}:
                    try:
                        metadata = json.loads(metadata_json)
                    except json.JSONDecodeError:
                        LOGGER.warning("Failed to decode calibration metadata from %s", archive_path)
                        metadata = {}
        return confusion, metadata

    def apply(self, counts: Dict[str, int]) -> Dict[str, float]:
        """
        Apply mitigation to measurement counts.

        Args:
            counts: Raw measurement counts

        Returns:
            Mitigated (possibly non-integer) counts
        """
        if self.confusion_matrix is None:
            raise ValueError("Must calibrate before applying mitigation")

        num_states = self.confusion_matrix.shape[0]
        num_qubits = int(np.log2(num_states))

        counts_vector = np.zeros(num_states, dtype=float)
        for bitstring, count in counts.items():
            state_index = self._bitstring_to_index(bitstring)
            counts_vector[state_index] += count

        total_counts = counts_vector.sum()
        if total_counts == 0:
            return {}

        measured_probabilities = counts_vector / total_counts

        try:
            inverse_confusion = np.linalg.inv(self.confusion_matrix)
        except np.linalg.LinAlgError:
            inverse_confusion = np.linalg.pinv(self.confusion_matrix)

        corrected_probabilities = inverse_confusion @ measured_probabilities
        corrected_probabilities = np.clip(corrected_probabilities, 0.0, None)

        probability_sum = corrected_probabilities.sum()
        if probability_sum > 0:
            corrected_probabilities = corrected_probabilities / probability_sum

        mitigated_counts = corrected_probabilities * total_counts

        mitigated_dict: Dict[str, float] = {}
        for state_index, value in enumerate(mitigated_counts):
            if value <= 1e-12:
                continue
            bitstring = self._index_to_bitstring(state_index, num_qubits)
            mitigated_dict[bitstring] = float(value)

        return mitigated_dict

    @staticmethod
    def _bitstring_to_index(bitstring: str) -> int:
        """Map a Qiskit-style bitstring to integer index (little-endian)."""

        index = 0
        for qubit_idx, bit in enumerate(reversed(bitstring)):
            if bit == "1":
                index |= 1 << qubit_idx
        return index

    @staticmethod
    def _index_to_bitstring(index: int, num_qubits: int) -> str:
        """Convert an index to Qiskit-style bitstring ordering."""

        return format(index, f"0{num_qubits}b")


@dataclass
class CalibrationRecord:
    """Persisted readout calibration details."""

    backend_name: str
    backend_version: Optional[str]
    qubits: tuple[int, ...]
    shots_per_state: int
    total_shots: int
    path: Path
    created_at: datetime
    confusion_matrix: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    reused: bool = False

    def to_mitigation_config(self, base_config: Optional["MitigationConfig"] = None):
        """Build a :class:`MitigationConfig` bound to this calibration."""

        from quartumse.reporting.manifest import MitigationConfig

        config = base_config.model_copy(deep=True) if base_config is not None else MitigationConfig()
        if "MEM" not in config.techniques:
            config.techniques.append("MEM")

        mem_qubits = list(self.qubits)
        config.parameters.setdefault("mem_qubits", mem_qubits)
        config.parameters.setdefault("mem_shots", self.shots_per_state)
        config.confusion_matrix_path = str(self.path.resolve())
        return config


class ReadoutCalibrationManager:
    """Coordinate measurement calibration reuse across experiments."""

    def __init__(self, base_dir: Union[str, Path] = Path("validation_data/calibrations")):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[Tuple[str, tuple[int, ...]], CalibrationRecord] = {}

    def ensure_calibration(
        self,
        backend: Backend,
        qubits: Sequence[int],
        *,
        shots: int = 4096,
        run_options: Optional[Dict[str, Any]] = None,
        force: bool = False,
        max_age: Optional[timedelta] = None,
    ) -> CalibrationRecord:
        """Return a calibration record, reusing disk artifacts when possible."""

        normalized_qubits = tuple(sorted(set(int(q) for q in qubits)))
        if not normalized_qubits:
            raise ValueError("At least one qubit must be specified for calibration")

        backend_name, backend_version = self._describe_backend(backend)
        key = (backend_name, normalized_qubits)

        cached = self._cache.get(key)
        if cached and not force and not self._is_expired(cached, max_age):
            cached.reused = True
            return cached

        archive_path = self._archive_path(backend_name, normalized_qubits)
        if not force and archive_path.exists():
            record = self._load_record_from_path(backend_name, backend_version, normalized_qubits, archive_path)
            if record and not self._is_expired(record, max_age):
                record.reused = True
                self._cache[key] = record
                return record

        metadata = {
            "backend_name": backend_name,
            "backend_version": backend_version,
            "qubits": list(normalized_qubits),
            "shots_per_state": shots,
            "total_shots": shots * (2 ** len(normalized_qubits)),
            "created_at": datetime.utcnow().isoformat(),
        }

        mem = MeasurementErrorMitigation(backend)
        saved_path = mem.calibrate(
            normalized_qubits,
            shots=shots,
            run_options=run_options,
            output_path=archive_path,
            metadata=metadata,
        )

        if saved_path is None:
            saved_path = archive_path

        record = CalibrationRecord(
            backend_name=backend_name,
            backend_version=backend_version,
            qubits=normalized_qubits,
            shots_per_state=metadata["shots_per_state"],
            total_shots=metadata["total_shots"],
            path=Path(saved_path).resolve(),
            created_at=datetime.fromisoformat(metadata["created_at"]),
            confusion_matrix=np.asarray(mem.confusion_matrix) if mem.confusion_matrix is not None else np.empty((0, 0)),
            metadata=metadata,
            reused=False,
        )
        self._cache[key] = record
        return record

    def _describe_backend(self, backend: Backend) -> Tuple[str, Optional[str]]:
        """Return sanitized backend name and version."""

        raw_name = None
        if hasattr(backend, "name"):
            try:
                raw_name = backend.name() if callable(backend.name) else backend.name
            except Exception:  # pragma: no cover - defensive against backend APIs
                raw_name = None

        backend_version = None
        configuration = None
        if hasattr(backend, "configuration"):
            try:
                configuration = backend.configuration()
            except Exception:  # pragma: no cover - best effort snapshot
                configuration = None

        if configuration is not None:
            raw_name = getattr(configuration, "backend_name", raw_name)
            backend_version = getattr(configuration, "backend_version", None)

        if raw_name is None:
            raw_name = getattr(backend, "__class__", type(backend)).__name__

        safe_name = self._sanitize(raw_name)
        if isinstance(backend_version, str):
            backend_version = backend_version.strip() or None

        return safe_name, backend_version

    def _archive_path(self, backend_name: str, qubits: tuple[int, ...]) -> Path:
        qubit_fragment = "-".join(str(q) for q in qubits)
        return self.base_dir / backend_name / f"q{qubit_fragment}" / "confusion_matrix.npz"

    def _load_record_from_path(
        self,
        backend_name: str,
        backend_version: Optional[str],
        qubits: tuple[int, ...],
        path: Path,
    ) -> Optional[CalibrationRecord]:
        try:
            confusion, metadata = MeasurementErrorMitigation._read_confusion_archive(path)
        except FileNotFoundError:
            return None

        created_at = metadata.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at_dt = datetime.fromisoformat(created_at)
            except ValueError:
                created_at_dt = datetime.utcfromtimestamp(path.stat().st_mtime)
        else:
            created_at_dt = datetime.utcfromtimestamp(path.stat().st_mtime)

        shots_per_state = int(metadata.get("shots_per_state", 0))
        total_shots = int(metadata.get("total_shots", 0))
        if total_shots <= 0 and shots_per_state > 0:
            total_shots = shots_per_state * (2 ** len(qubits))

        record = CalibrationRecord(
            backend_name=backend_name,
            backend_version=backend_version,
            qubits=qubits,
            shots_per_state=shots_per_state,
            total_shots=total_shots,
            path=path.resolve(),
            created_at=created_at_dt,
            confusion_matrix=np.asarray(confusion, dtype=float),
            metadata=metadata,
            reused=False,
        )
        self._cache[(backend_name, qubits)] = record
        return record

    def _is_expired(self, record: CalibrationRecord, max_age: Optional[timedelta]) -> bool:
        if max_age is None:
            return False
        return datetime.utcnow() - record.created_at > max_age

    @staticmethod
    def _sanitize(value: str) -> str:
        safe = []
        for char in value:
            if char.isalnum() or char in {"_", "-", "."}:
                safe.append(char)
            else:
                safe.append("_")
        collapsed = "".join(safe).strip("_")
        return collapsed or "backend"

