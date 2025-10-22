"""IBM Quantum connector utilities.

This module provides a small abstraction layer for interacting with IBM Quantum
resources via Qiskit Runtime.  It focuses on supplying ready-to-use backend
objects together with helper utilities for the Runtime Primitives interface
used throughout QuartumSE.  When a managed IBM backend is resolved, a
``SamplerV2`` instance can be constructed to submit circuits using the new
primitive API.  Local Aer simulators are still supported as fallbacks.

The connector performs three primary tasks:

1.  Authenticate with IBM Quantum using environment variables or a supplied
    configuration dictionary.
2.  Resolve a backend by name and supply a ``Backend`` instance with a ``run``
    method compatible with the rest of QuartumSE.
3.  Capture a calibration snapshot (T1/T2, gate errors, readout errors) for the
    resolved backend so provenance manifests can record the calibration state
    associated with each experiment.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from qiskit.providers.backend import Backend
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService

try:  # Runtime primitive import is optional during documentation builds/tests
    from qiskit_ibm_runtime import SamplerV2
except Exception:  # pragma: no cover - fallback when primitive class unavailable
    SamplerV2 = None  # type: ignore

try:  # Runtime import is optional during documentation builds/tests
    from qiskit_ibm_runtime.exceptions import IBMRuntimeError
except Exception:  # pragma: no cover - fallback when exception class unavailable
    IBMRuntimeError = Exception  # type: ignore

from quartumse.reporting.manifest import BackendSnapshot

LOGGER = logging.getLogger(__name__)

# Supported environment variable aliases for IBM Quantum authentication.
_ENV_TOKEN_KEYS = (
    "QISKIT_IBM_TOKEN",
    "QISKIT_RUNTIME_API_TOKEN",
    "IBM_QUANTUM_API_TOKEN",
)
_ENV_CHANNEL_KEYS = ("QISKIT_IBM_CHANNEL", "QISKIT_RUNTIME_CHANNEL")
_ENV_INSTANCE_KEYS = ("QISKIT_IBM_INSTANCE", "QISKIT_RUNTIME_INSTANCE")


@dataclass
class IBMBackendHandle:
    """Resolved backend together with its calibration snapshot."""

    backend: Backend
    snapshot: BackendSnapshot
    service: Optional[QiskitRuntimeService] = None


def is_ibm_runtime_backend(backend: Backend) -> bool:
    """Return ``True`` when ``backend`` originates from IBM Runtime."""

    module_name = getattr(type(backend), "__module__", "")
    return "qiskit_ibm_runtime" in module_name


def create_runtime_sampler(backend: Backend):
    """Instantiate ``SamplerV2`` for ``backend`` when supported."""

    if SamplerV2 is None or not is_ibm_runtime_backend(backend):
        return None

    try:
        return SamplerV2(mode=backend)
    except Exception as exc:  # pragma: no cover - requires remote service
        LOGGER.warning(
            "Unable to initialise SamplerV2 for backend %s (%s)",
            getattr(backend, "name", backend),
            exc,
        )
        return None


def _read_first_env(*keys: str) -> Optional[str]:
    """Return the first populated environment variable from ``keys``."""

    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return None


def _coerce_datetime(value: Any) -> Optional[datetime]:
    """Convert assorted timestamp formats into ``datetime`` objects."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (list, tuple)) and value:
        # Some IBM APIs return ``[datetime, datetime]`` for timezone aware pairs.
        return _coerce_datetime(value[0])
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def create_backend_snapshot(backend: Backend) -> BackendSnapshot:
    """Create a :class:`BackendSnapshot` for ``backend``.

    The snapshot captures configuration information and available calibration
    metrics.  When calibration data are unavailable (e.g., for the local Aer
    simulator) the associated fields are omitted, but a deterministic
    ``properties_hash`` is still provided to make manifest diffs stable.
    """

    try:
        configuration = backend.configuration()
    except Exception:  # pragma: no cover - some mock backends raise
        configuration = None

    basis_gates = []
    coupling_map = None
    num_qubits = 0
    if configuration is not None:
        basis_gates = list(getattr(configuration, "basis_gates", []) or [])
        coupling_map = getattr(configuration, "coupling_map", None)
        num_qubits = int(
            getattr(configuration, "n_qubits", getattr(configuration, "num_qubits", 0))
            or 0
        )

    calibration_timestamp = datetime.utcnow()
    t1_times: Dict[int, float] = {}
    t2_times: Dict[int, float] = {}
    readout_errors: Dict[int, float] = {}
    gate_error_totals: Dict[str, float] = {}
    gate_error_counts: Dict[str, int] = {}
    properties_hash = ""

    try:
        properties = backend.properties()
    except Exception:
        properties = None

    if properties is not None:
        timestamp = _coerce_datetime(getattr(properties, "last_update_date", None))
        if timestamp is not None:
            calibration_timestamp = timestamp

        # ``to_dict`` occasionally includes datetimes which are not JSON
        # serializable by default.  ``default=str`` ensures stability.
        try:
            props_dict = properties.to_dict()
            properties_hash = hashlib.sha256(
                json.dumps(props_dict, sort_keys=True, default=str).encode()
            ).hexdigest()
        except Exception:  # pragma: no cover - defensive against provider changes
            properties_hash = ""

        # Extract qubit-level metrics
        for qubit_index, qubit_data in enumerate(getattr(properties, "qubits", []) or []):
            for entry in qubit_data:
                name = getattr(entry, "name", "").lower()
                value = getattr(entry, "value", None)
                if value is None:
                    continue
                if name == "t1":
                    t1_times[qubit_index] = float(value)
                elif name == "t2":
                    t2_times[qubit_index] = float(value)
                elif name == "readout_error":
                    readout_errors[qubit_index] = float(value)

        # Aggregate gate error metrics
        for gate in getattr(properties, "gates", []) or []:
            gate_name = getattr(gate, "gate", getattr(gate, "name", ""))
            for param in getattr(gate, "parameters", []) or []:
                if getattr(param, "name", "").lower() == "gate_error":
                    gate_error_totals[gate_name] = gate_error_totals.get(gate_name, 0.0) + float(
                        getattr(param, "value", 0.0)
                    )
                    gate_error_counts[gate_name] = gate_error_counts.get(gate_name, 0) + 1

    gate_errors = {
        gate_name: gate_error_totals[gate_name] / gate_error_counts[gate_name]
        for gate_name in gate_error_totals
        if gate_error_counts[gate_name]
    }

    backend_version = getattr(backend, "version", "unknown")
    if not isinstance(backend_version, str):
        backend_version = str(backend_version)

    snapshot = BackendSnapshot(
        backend_name=getattr(backend, "name", "unknown"),
        backend_version=backend_version,
        num_qubits=num_qubits,
        coupling_map=coupling_map,
        basis_gates=basis_gates,
        t1_times=t1_times or None,
        t2_times=t2_times or None,
        gate_errors=gate_errors or None,
        readout_errors=readout_errors or None,
        calibration_timestamp=calibration_timestamp,
        properties_hash=properties_hash,
    )
    return snapshot


class IBMBackendConnector:
    """Lightweight helper for resolving IBM Quantum backends."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._service: Optional[QiskitRuntimeService] = None

    def _build_service_kwargs(self) -> Dict[str, Any]:
        """Collect keyword arguments for :class:`QiskitRuntimeService`."""

        kwargs: Dict[str, Any] = {}

        token = self.config.get("token") or _read_first_env(*_ENV_TOKEN_KEYS)
        channel = self.config.get("channel") or _read_first_env(*_ENV_CHANNEL_KEYS)
        instance = self.config.get("instance") or _read_first_env(*_ENV_INSTANCE_KEYS)

        if token:
            kwargs["token"] = token
        if channel:
            kwargs["channel"] = channel
        if instance:
            kwargs["instance"] = instance

        # ``url`` is used by legacy accounts; honour it if provided explicitly.
        if "url" in self.config:
            kwargs["url"] = self.config["url"]

        return kwargs

    def _get_service(self) -> Optional[QiskitRuntimeService]:
        """Instantiate (or reuse) the runtime service."""

        if self._service is not None:
            return self._service

        kwargs = self._build_service_kwargs()
        try:
            if kwargs:
                self._service = QiskitRuntimeService(**kwargs)
            else:
                self._service = QiskitRuntimeService()
        except Exception as exc:  # pragma: no cover - requires remote service
            LOGGER.warning(
                "Unable to initialise QiskitRuntimeService (%s). Falling back to local simulators when possible.",
                exc,
            )
            self._service = None
        return self._service

    def connect(self, backend_name: str) -> IBMBackendHandle:
        """Resolve ``backend_name`` to a backend and calibration snapshot."""

        backend: Optional[Backend] = None
        service = self._get_service()
        if service is not None:
            try:
                backend = service.backend(backend_name)
            except IBMRuntimeError as exc:  # pragma: no cover - requires remote call
                LOGGER.warning("IBM Runtime backend lookup failed for %s (%s)", backend_name, exc)
            except Exception as exc:  # pragma: no cover - defensive fallback
                LOGGER.warning("Unexpected error fetching backend %s (%s)", backend_name, exc)

        if backend is None:
            if backend_name in {"aer_simulator", "ibmq_qasm_simulator", "simulator"}:
                LOGGER.info(
                    "Using local AerSimulator fallback for backend '%s'", backend_name
                )
                backend = AerSimulator()
            else:
                raise ValueError(
                    f"Unable to resolve IBM backend '{backend_name}'. Ensure credentials are configured or use a simulator."
                )

        snapshot = create_backend_snapshot(backend)
        return IBMBackendHandle(backend=backend, snapshot=snapshot, service=service)


def resolve_backend_descriptor(descriptor: str, config: Optional[Dict[str, Any]] = None) -> IBMBackendHandle:
    """Resolve a ``provider:backend`` descriptor.

    Currently only the ``ibm`` provider is implemented, but the descriptor
    format matches the long-term multi-provider roadmap.
    """

    provider, _, backend_name = descriptor.partition(":")
    provider = provider.lower().strip()
    backend_name = backend_name.strip()

    if provider != "ibm" or not backend_name:
        raise ValueError(f"Unsupported backend descriptor: {descriptor}")

    connector = IBMBackendConnector(config=config)
    return connector.connect(backend_name)


__all__ = [
    "IBMBackendConnector",
    "IBMBackendHandle",
    "create_backend_snapshot",
    "create_runtime_sampler",
    "is_ibm_runtime_backend",
    "resolve_backend_descriptor",
]
