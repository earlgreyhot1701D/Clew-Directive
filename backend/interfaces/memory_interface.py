"""
Memory interface for Clew Directive session context.

MVP: In-memory dict within Lambda execution context.
Future: AgentCore Memory for cross-invocation session state.

Contract:
    store(key, value) → None
    retrieve(key) → value or None
    clear() → None
"""

from abc import ABC, abstractmethod
from typing import Any


class MemoryInterface(ABC):
    """Abstract memory contract."""

    @abstractmethod
    def store(self, key: str, value: Any) -> None:
        """Store a value in session memory."""
        ...

    @abstractmethod
    def retrieve(self, key: str) -> Any | None:
        """Retrieve a value from session memory. Returns None if not found."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all session memory. Called after PDF delivery."""
        ...


class InMemorySession(MemoryInterface):
    """
    MVP implementation: simple dict.

    Lives within a single Lambda invocation. Data is automatically
    purged when Lambda execution ends. This IS the zero-data architecture.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def store(self, key: str, value: Any) -> None:
        self._store[key] = value

    def retrieve(self, key: str) -> Any | None:
        return self._store.get(key)

    def clear(self) -> None:
        self._store.clear()


# TODO: Future implementation
# class AgentCoreMemory(MemoryInterface):
#     """
#     Future: AgentCore Memory client for cross-invocation session state.
#     Swap this in by changing the factory function below.
#     """
#     pass


def create_memory() -> MemoryInterface:
    """Factory: returns the active memory implementation."""
    return InMemorySession()
