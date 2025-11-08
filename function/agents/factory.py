"""Factory for creating and configuring agents."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class AgentConfig:
    """Configuration for creating an agent."""

    name: str
    role: str
    system_message: str
    tools: list[str]
    max_consecutive_auto_reply: int = 10
    temperature: float = 0.0


class AgentFactory:
    """Factory for creating configured agents."""

    def __init__(self, registry: ToolRegistry) -> None:
        """Initialize factory with tool registry.

        Args:
            registry: ToolRegistry instance for accessing tools.
        """
        self.registry = registry
        self.llm_config = self._build_llm_config()

    def _build_llm_config(self) -> dict:
        """Build LLM configuration from environment variables.

        Returns:
            Dictionary with LLM configuration for AG2.
        """
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M")

        return {
            "config_list": [
                {
                    "model": model,
                    "api_base": ollama_base_url,
                    "api_type": "open_ai",
                    "api_key": "ollama",
                }
            ],
            "temperature": 0.0,
            "timeout": 120,
            "cache_seed": None,
        }

    def create_agent(self, config: AgentConfig) -> "Any":
        """Create an agent with specified configuration.

        Args:
            config: AgentConfig instance with agent parameters.

        Returns:
            Configured AssistantAgent instance.

        Raises:
            ValueError: If referenced tools do not exist in registry.
        """
        # Validate that all tools exist
        missing_tools = [t for t in config.tools if not self.registry.has(t)]
        if missing_tools:
            raise ValueError(
                f"Tools not found in registry: {', '.join(missing_tools)}"
            )

        logger.info(f"Creating agent: {config.name} with tools: {config.tools}")

        # Import here to avoid circular dependencies and lazy loading
        # This will use AG2 at runtime
        try:
            from autogen import AssistantAgent

            agent = AssistantAgent(
                name=config.name,
                system_message=config.system_message,
                llm_config=self.llm_config,
                max_consecutive_auto_reply=config.max_consecutive_auto_reply,
            )
            return agent
        except ImportError as e:
            logger.error(f"Failed to import AssistantAgent: {e}")
            raise RuntimeError("AG2 (autogen) is not installed") from e
