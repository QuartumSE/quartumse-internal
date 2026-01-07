"""Classical Shadows as Protocol implementations.

This module wraps the classical shadows implementations (v0, v1, etc.)
as Protocol ABC implementations, enabling unified benchmarking with
the direct measurement baselines.
"""

from quartumse.protocols.shadows.shadows_protocol import (
    ClassicalShadowsProtocol,
    ShadowsV0Protocol,
    ShadowsV1Protocol,
)

__all__ = [
    "ClassicalShadowsProtocol",
    "ShadowsV0Protocol",
    "ShadowsV1Protocol",
]
