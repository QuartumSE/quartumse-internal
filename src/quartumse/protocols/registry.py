"""Protocol registry for managing measurement protocols (§14.3).

This module provides a registry for measurement protocols that enables:
- Registration of protocols with unique IDs and versions
- Lookup of protocols by ID
- Version tracking for reproducibility
- Deprecation handling

All protocols must be registered before use in benchmarks to ensure
reproducibility and proper provenance tracking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Protocol


class ProtocolRegistry:
    """Registry for measurement protocols.

    This singleton registry maintains a mapping of protocol IDs to
    protocol classes, enabling lookup and instantiation by ID.

    Usage:
        # Register a protocol
        registry = ProtocolRegistry()
        registry.register(MyProtocol)

        # Get a protocol class
        protocol_cls = registry.get("my_protocol")
        protocol = protocol_cls(config)

        # List all registered protocols
        for proto_id in registry.list_protocols():
            print(proto_id)
    """

    _instance: ProtocolRegistry | None = None
    _protocols: dict[str, type[Protocol]]

    def __new__(cls) -> ProtocolRegistry:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._protocols = {}
        return cls._instance

    def register(self, protocol_cls: type[Protocol]) -> None:
        """Register a protocol class.

        Args:
            protocol_cls: Protocol class to register. Must have protocol_id
                and protocol_version class attributes.

        Raises:
            ValueError: If protocol_id is already registered with a different class.
        """
        protocol_id = protocol_cls.protocol_id
        if protocol_id in self._protocols:
            existing = self._protocols[protocol_id]
            if existing is not protocol_cls:
                raise ValueError(
                    f"Protocol ID '{protocol_id}' already registered to "
                    f"{existing.__name__}, cannot register {protocol_cls.__name__}"
                )
        self._protocols[protocol_id] = protocol_cls

    def get(self, protocol_id: str) -> type[Protocol]:
        """Get a protocol class by ID.

        Args:
            protocol_id: The protocol identifier.

        Returns:
            The protocol class.

        Raises:
            KeyError: If protocol_id is not registered.
        """
        if protocol_id not in self._protocols:
            available = ", ".join(sorted(self._protocols.keys()))
            raise KeyError(
                f"Protocol '{protocol_id}' not found. "
                f"Available protocols: {available or '(none)'}"
            )
        return self._protocols[protocol_id]

    def list_protocols(self) -> list[str]:
        """List all registered protocol IDs."""
        return sorted(self._protocols.keys())

    def get_info(self, protocol_id: str) -> dict[str, str]:
        """Get information about a registered protocol.

        Args:
            protocol_id: The protocol identifier.

        Returns:
            Dict with protocol_id, protocol_version, and class name.
        """
        protocol_cls = self.get(protocol_id)
        return {
            "protocol_id": protocol_cls.protocol_id,
            "protocol_version": protocol_cls.protocol_version,
            "class_name": protocol_cls.__name__,
            "module": protocol_cls.__module__,
        }

    def clear(self) -> None:
        """Clear all registered protocols (for testing)."""
        self._protocols.clear()


# Global registry instance
_registry = ProtocolRegistry()


def register_protocol(protocol_cls: type[Protocol]) -> type[Protocol]:
    """Decorator to register a protocol class.

    Usage:
        @register_protocol
        class MyProtocol(Protocol):
            protocol_id = "my_protocol"
            protocol_version = "1.0.0"
            ...
    """
    _registry.register(protocol_cls)
    return protocol_cls


def get_protocol(protocol_id: str) -> type[Protocol]:
    """Get a protocol class by ID from the global registry."""
    return _registry.get(protocol_id)


def list_protocols() -> list[str]:
    """List all registered protocol IDs from the global registry."""
    return _registry.list_protocols()


def get_registry() -> ProtocolRegistry:
    """Get the global protocol registry instance."""
    return _registry
