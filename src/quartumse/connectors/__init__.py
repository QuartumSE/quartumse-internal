"""Backend connectors for multi-cloud quantum providers."""

from typing import Dict, Optional, Tuple

from qiskit.providers.backend import Backend

from quartumse.reporting.manifest import BackendSnapshot

from .ibm import (
    IBMBackendConnector,
    IBMBackendHandle,
    create_backend_snapshot,
    create_runtime_sampler,
    is_ibm_runtime_backend,
    resolve_backend_descriptor,
    SamplerPrimitive,
)
from .topology import get_linear_chain


def resolve_backend(
    descriptor: str,
    *,
    config: Optional[Dict[str, str]] = None,
) -> Tuple[Backend, BackendSnapshot]:
    """Resolve a connector descriptor into a backend and snapshot."""

    handle = resolve_backend_descriptor(descriptor, config=config)
    return handle.backend, handle.snapshot


__all__ = [
    "IBMBackendConnector",
    "IBMBackendHandle",
    "create_backend_snapshot",
    "create_runtime_sampler",
    "get_linear_chain",
    "is_ibm_runtime_backend",
    "resolve_backend",
    "resolve_backend_descriptor",
    "SamplerPrimitive",
]
