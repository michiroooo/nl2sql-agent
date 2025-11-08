"""Base orchestrator with dependency injection support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from function.core.config import AppConfig
from function.core.logging import StructuredLogger
from function.tools.registry import ToolRegistry
from function.agents.factory import AgentFactory


class OrchestratorBase(ABC):
    """Base class for orchestrators with dependency injection."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        agent_factory: AgentFactory,
        app_config: AppConfig,
        logger: StructuredLogger,
    ) -> None:
        """Initialize orchestrator with injected dependencies.

        Args:
            tool_registry: Central tool registry.
            agent_factory: Factory for creating agents.
            app_config: Application configuration.
            logger: Structured logger instance.
        """
        self.tool_registry = tool_registry
        self.agent_factory = agent_factory
        self.app_config = app_config
        self.logger = logger

        self.logger.info(
            "Orchestrator initialized",
            tools_count=len(self.tool_registry.list_all()),
            phoenix_enabled=self.app_config.phoenix.enabled,
        )

    @abstractmethod
    def execute(self, query: str) -> dict[str, Any]:
        """Execute query.

        Args:
            query: User query.

        Returns:
            Execution result.
        """
        pass
