"""Measurement protocols for quantum observable estimation.

This package implements the protocol interface defined in Measurements Bible §5.
All protocols follow a common contract:

1. initialize(observable_set, total_budget, seed) -> ProtocolState
2. next_plan(state, remaining_budget) -> MeasurementPlan
3. acquire(circuit, plan, backend, seed) -> RawDatasetChunk
4. update(state, data_chunk) -> ProtocolState
5. finalize(state, observable_set) -> Estimates

Protocols are categorized into:
- Direct measurement protocols (§4.1): direct_naive, direct_grouped, direct_optimized
- Classical shadows protocols (§4.2): shadows_local, shadows_local_mem, shadows_global

Usage:
    from quartumse.protocols import get_protocol, list_protocols
    from quartumse.protocols.base import ProtocolConfig

    # List available protocols
    print(list_protocols())

    # Get and instantiate a protocol
    protocol_cls = get_protocol("shadows_local")
    config = ProtocolConfig(confidence_level=0.95, random_seed=42)
    protocol = protocol_cls(config)

    # Run the protocol
    estimates = protocol.run(circuit, observable_set, budget, backend)
"""

from .base import (
    AdaptiveProtocol,
    Protocol,
    ProtocolConfig,
    StaticProtocol,
)

# Import baseline protocols (triggers registration)
from .baselines import (
    DirectGroupedProtocol,
    DirectGroupedState,
    DirectNaiveProtocol,
    DirectNaiveState,
    DirectOptimizedProtocol,
    DirectOptimizedState,
)
from .registry import (
    get_protocol,
    get_registry,
    list_protocols,
    register_protocol,
)

# Import shadows protocols (triggers registration)
from .shadows import (
    ClassicalShadowsProtocol,
    ShadowsV0Protocol,
    ShadowsV1Protocol,
)
from .state import (
    CIMethod,
    CIResult,
    Estimates,
    MeasurementPlan,
    MeasurementSetting,
    ObservableEstimate,
    ProtocolState,
    RawDatasetChunk,
)

__all__ = [
    # Base classes
    "Protocol",
    "StaticProtocol",
    "AdaptiveProtocol",
    "ProtocolConfig",
    # State and data structures
    "ProtocolState",
    "MeasurementPlan",
    "MeasurementSetting",
    "RawDatasetChunk",
    "Estimates",
    "ObservableEstimate",
    "CIResult",
    "CIMethod",
    # Registry
    "register_protocol",
    "get_protocol",
    "list_protocols",
    "get_registry",
    # Baseline protocols
    "DirectNaiveProtocol",
    "DirectNaiveState",
    "DirectGroupedProtocol",
    "DirectGroupedState",
    "DirectOptimizedProtocol",
    "DirectOptimizedState",
    # Shadows protocols
    "ClassicalShadowsProtocol",
    "ShadowsV0Protocol",
    "ShadowsV1Protocol",
]
