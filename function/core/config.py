"""Configuration management for the application."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class PhoenixConfig:
    """Phoenix observability configuration."""

    collector_endpoint: str
    project_name: str = "ag2-multi-agent"
    enabled: bool = True

    @classmethod
    def from_env(cls) -> PhoenixConfig:
        """Create configuration from environment variables.

        Returns:
            PhoenixConfig instance with values from environment.
        """
        return cls(
            collector_endpoint=os.getenv(
                "PHOENIX_COLLECTOR_ENDPOINT",
                "http://phoenix:4317"
            ),
            project_name=os.getenv("PHOENIX_PROJECT_NAME", "ag2-multi-agent"),
            enabled=os.getenv("PHOENIX_ENABLED", "true").lower() == "true"
        )


@dataclass(slots=True, frozen=True)
class MCPConfig:
    """MCP server configuration."""

    server_url: str
    timeout: int = 30
    use_fallback: bool = True

    @classmethod
    def from_env(cls) -> MCPConfig:
        """Create configuration from environment variables.

        Returns:
            MCPConfig instance with values from environment.
        """
        return cls(
            server_url=os.getenv("MCP_SERVER_URL", "http://mcp-server:8080/mcp"),
            timeout=int(os.getenv("MCP_TIMEOUT", "30")),
            use_fallback=os.getenv("MCP_USE_FALLBACK", "true").lower() == "true"
        )


@dataclass(slots=True, frozen=True)
class OllamaConfig:
    """Ollama LLM server configuration."""

    model: str
    host: str = "localhost"
    port: int = 11434

    @property
    def endpoint(self) -> str:
        """Get full HTTP endpoint for Ollama server.

        Returns:
            Full URL to Ollama server.
        """
        return f"http://{self.host}:{self.port}"

    @property
    def api_endpoint(self) -> str:
        """Get API endpoint for OpenAI-compatible interface.

        Returns:
            Full URL to Ollama API endpoint.
        """
        return f"{self.endpoint}/v1"

    @classmethod
    def from_env(cls) -> OllamaConfig:
        """Create configuration from environment variables.

        Returns:
            OllamaConfig instance with values from environment.
        """
        return cls(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M"),
            host=os.getenv("OLLAMA_HOST", "localhost"),
            port=int(os.getenv("OLLAMA_PORT", "11434"))
        )


@dataclass(slots=True, frozen=True)
class DatabaseConfig:
    """Database configuration."""

    path: str

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Create configuration from environment variables.

        Returns:
            DatabaseConfig instance with values from environment.
        """
        return cls(
            path=os.getenv(
                "DATABASE_PATH",
                "/app/data/ecommerce.db"
            )
        )


@dataclass(slots=True, frozen=True)
class AppConfig:
    """Main application configuration."""

    phoenix: PhoenixConfig
    mcp: MCPConfig
    ollama: OllamaConfig
    database: DatabaseConfig

    @classmethod
    def from_env(cls) -> AppConfig:
        """Create configuration from environment variables.

        Returns:
            AppConfig instance with all sub-configurations.
        """
        return cls(
            phoenix=PhoenixConfig.from_env(),
            mcp=MCPConfig.from_env(),
            ollama=OllamaConfig.from_env(),
            database=DatabaseConfig.from_env()
        )

    def validate(self) -> bool:
        """Validate all configuration values.

        Returns:
            True if all configurations are valid.

        Raises:
            ValueError: If any configuration is invalid.
        """
        if not self.phoenix.collector_endpoint:
            raise ValueError("PHOENIX_COLLECTOR_ENDPOINT is required")

        if not self.mcp.server_url:
            raise ValueError("MCP_SERVER_URL is required")

        if not self.ollama.model:
            raise ValueError("OLLAMA_MODEL is required")

        if not self.database.path:
            raise ValueError("DATABASE_PATH is required")

        logger.info("Configuration validation passed")
        return True
