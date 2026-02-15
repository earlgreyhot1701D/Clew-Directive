"""
Tool registry interface for Clew Directive.

MVP: Direct function calls — Scout and Navigator invoke tools directly.
Future: AgentCore Gateway with MCP-compatible tool registration.

Contract:
    register_tool(name, callable) → None
    invoke_tool(name, **kwargs) → result
    list_tools() → list[str]
"""

from abc import ABC, abstractmethod
from typing import Any, Callable


class ToolRegistryInterface(ABC):
    """Abstract tool registry contract."""

    @abstractmethod
    def register_tool(self, name: str, tool_fn: Callable) -> None:
        """Register a tool by name."""
        ...

    @abstractmethod
    def invoke_tool(self, name: str, **kwargs: Any) -> Any:
        """Invoke a registered tool by name."""
        ...

    @abstractmethod
    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        ...


class DirectCallRegistry(ToolRegistryInterface):
    """
    MVP implementation: direct function call registry.

    Tools are Python functions registered by name. Agents call them
    directly through this registry. No network overhead, no MCP protocol.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}

    def register_tool(self, name: str, tool_fn: Callable) -> None:
        self._tools[name] = tool_fn

    def invoke_tool(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered. Available: {list(self._tools.keys())}")
        return self._tools[name](**kwargs)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


# TODO: Future implementation
# class AgentCoreGatewayRegistry(ToolRegistryInterface):
#     """Future: AgentCore Gateway with MCP-compatible tool registration."""
#     pass


def create_tool_registry() -> ToolRegistryInterface:
    """Factory: returns the active tool registry implementation."""
    return DirectCallRegistry()
