"""Custom exceptions for AgentOps."""

from __future__ import annotations


class AgentOpsError(Exception):
    """Base exception for all AgentOps errors."""

    pass


class MCPConnectionError(AgentOpsError):
    """Raised when MCP server connection fails."""

    def __init__(self, endpoint: str, details: str) -> None:
        """Initialize MCP connection error.

        Args:
            endpoint: The MCP server endpoint that failed.
            details: Additional error details.
        """
        self.endpoint = endpoint
        self.details = details
        super().__init__(
            f"MCP connection failed at {endpoint}: {details}"
        )


class DatabaseError(AgentOpsError):
    """Raised when database operations fail."""

    def __init__(self, operation: str, error: str) -> None:
        """Initialize database error.

        Args:
            operation: The database operation that failed.
            error: The error message.
        """
        self.operation = operation
        self.error = error
        super().__init__(f"Database {operation} failed: {error}")


class AgentExecutionError(AgentOpsError):
    """Raised when agent execution fails."""

    def __init__(self, agent_name: str, query: str, error: str) -> None:
        """Initialize agent execution error.

        Args:
            agent_name: The name of the agent that failed.
            query: The query that was being executed.
            error: The error message.
        """
        self.agent_name = agent_name
        self.query = query
        self.error = error
        super().__init__(
            f"Agent '{agent_name}' failed executing query '{query}': {error}"
        )


class ToolRegistrationError(AgentOpsError):
    """Raised when tool registration fails."""

    def __init__(self, tool_name: str, reason: str) -> None:
        """Initialize tool registration error.

        Args:
            tool_name: The name of the tool that failed to register.
            reason: The reason for the failure.
        """
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Failed to register tool '{tool_name}': {reason}")


class ConfigurationError(AgentOpsError):
    """Raised when configuration is invalid."""

    def __init__(self, config_key: str, message: str) -> None:
        """Initialize configuration error.

        Args:
            config_key: The configuration key that caused the error.
            message: The error message.
        """
        self.config_key = config_key
        self.message = message
        super().__init__(f"Configuration error for '{config_key}': {message}")
