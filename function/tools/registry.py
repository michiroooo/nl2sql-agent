"""Tool registry for managing and accessing tools in the system."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ToolDefinition:
    """Definition of a tool with metadata and implementation."""

    name: str
    description: str
    func: Callable
    input_schema: dict[str, Any]

    def __call__(self, **kwargs: Any) -> Any:
        """Execute the tool with given arguments."""
        return self.func(**kwargs)


class ToolRegistry:
    """Central registry for managing tools."""

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        """Register a new tool in the registry.

        Args:
            definition: ToolDefinition instance to register.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if definition.name in self._tools:
            raise ValueError(f"Tool '{definition.name}' is already registered.")

        self._tools[definition.name] = definition
        logger.info(f"Registered tool: {definition.name}")

    def get(self, name: str) -> ToolDefinition | None:
        """Retrieve a tool by name.

        Args:
            name: Tool name to retrieve.

        Returns:
            ToolDefinition if found, None otherwise.
        """
        return self._tools.get(name)

    def list_all(self) -> list[ToolDefinition]:
        """Get all registered tools.

        Returns:
            List of all ToolDefinition instances.
        """
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        """Get all tool names.

        Returns:
            List of registered tool names.
        """
        return list(self._tools.keys())

    def has(self, name: str) -> bool:
        """Check if a tool exists.

        Args:
            name: Tool name to check.

        Returns:
            True if tool exists, False otherwise.
        """
        return name in self._tools

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        logger.info("Tool registry cleared")
