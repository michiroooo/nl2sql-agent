"""Structured logging for agent operations."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogContext:
    """Logging context with execution metadata."""

    agent_name: str | None = None
    operation: str | None = None
    request_id: str | None = None
    timestamp: float | None = None
    duration_ms: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary.

        Returns:
            Dictionary representation of context.
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


class StructuredLogger:
    """Wrapper around Python logger for structured logging."""

    def __init__(self, name: str, context: LogContext | None = None) -> None:
        """Initialize logger with optional context.

        Args:
            name: Logger name (typically __name__).
            context: Optional logging context for additional metadata.
        """
        self._logger = logging.getLogger(name)
        self._context = context or LogContext()

    def _format_message(self, message: str, metadata: dict[str, Any] | None = None) -> str:
        """Format message with context and metadata.

        Args:
            message: Base log message.
            metadata: Optional additional metadata to include.

        Returns:
            Formatted message string.
        """
        context_data = self._context.to_dict()
        if metadata:
            context_data.update(metadata)

        if context_data:
            return f"{message} | {json.dumps(context_data)}"
        return message

    def log_agent_execution(
        self,
        agent_name: str,
        query: str,
        success: bool,
        duration_ms: float,
        error: str | None = None,
        response: str | None = None,
    ) -> None:
        """Log agent execution details.

        Args:
            agent_name: Name of the agent.
            query: Input query or prompt.
            success: Whether execution succeeded.
            duration_ms: Execution time in milliseconds.
            error: Optional error message if failed.
            response: Optional agent response.
        """
        metadata = {
            "agent": agent_name,
            "query": query[:100],
            "success": success,
            "duration_ms": duration_ms,
        }
        if error:
            metadata["error"] = error
        if response:
            metadata["response_length"] = len(response)

        level = logging.ERROR if not success else logging.INFO
        message = f"Agent execution: {agent_name}"
        self._logger.log(level, self._format_message(message, metadata))

    def log_mcp_call(
        self,
        tool_name: str,
        success: bool,
        duration_ms: float,
        error: str | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        """Log MCP tool call.

        Args:
            tool_name: Name of the tool.
            success: Whether call succeeded.
            duration_ms: Execution time in milliseconds.
            error: Optional error message if failed.
            args: Optional tool arguments.
        """
        metadata = {
            "tool": tool_name,
            "success": success,
            "duration_ms": duration_ms,
        }
        if error:
            metadata["error"] = error
        if args:
            metadata["args_count"] = len(args)

        level = logging.ERROR if not success else logging.DEBUG
        message = f"MCP tool call: {tool_name}"
        self._logger.log(level, self._format_message(message, metadata))

    def log_database_operation(
        self,
        operation: str,
        success: bool,
        duration_ms: float,
        query: str | None = None,
        error: str | None = None,
    ) -> None:
        """Log database operation.

        Args:
            operation: Type of operation (SELECT, INSERT, etc.).
            success: Whether operation succeeded.
            duration_ms: Execution time in milliseconds.
            query: Optional SQL query (truncated for logging).
            error: Optional error message if failed.
        """
        metadata = {
            "operation": operation,
            "success": success,
            "duration_ms": duration_ms,
        }
        if query:
            metadata["query_preview"] = query[:100]
        if error:
            metadata["error"] = error

        level = logging.ERROR if not success else logging.INFO
        message = f"Database operation: {operation}"
        self._logger.log(level, self._format_message(message, metadata))

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with context.

        Args:
            message: Log message.
            **kwargs: Additional metadata.
        """
        self._logger.debug(self._format_message(message, kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context.

        Args:
            message: Log message.
            **kwargs: Additional metadata.
        """
        self._logger.info(self._format_message(message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context.

        Args:
            message: Log message.
            **kwargs: Additional metadata.
        """
        self._logger.warning(self._format_message(message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with context.

        Args:
            message: Log message.
            **kwargs: Additional metadata.
        """
        self._logger.error(self._format_message(message, kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with context.

        Args:
            message: Log message.
            **kwargs: Additional metadata.
        """
        self._logger.critical(self._format_message(message, kwargs))

    def set_context(self, **kwargs: Any) -> None:
        """Update logging context.

        Args:
            **kwargs: Context fields to update (agent_name, operation, request_id, etc.).
        """
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                object.__setattr__(self._context, key, value)

    def time_operation(self, operation_name: str) -> _OperationTimer:
        """Create context manager for timing operations.

        Args:
            operation_name: Name of operation to time.

        Returns:
            Context manager for automatic duration tracking.

        Example:
            with logger.time_operation("database_query") as timer:
                # perform operation
                pass
            # Duration automatically logged
        """
        return _OperationTimer(self, operation_name)


class _OperationTimer:
    """Context manager for timing operations with automatic logging."""

    def __init__(self, logger: StructuredLogger, operation_name: str) -> None:
        """Initialize timer.

        Args:
            logger: StructuredLogger instance.
            operation_name: Name of operation.
        """
        self._logger = logger
        self._operation_name = operation_name
        self._start_time: float | None = None
        self._duration_ms: float | None = None

    def __enter__(self) -> _OperationTimer:
        """Start timing.

        Returns:
            Self for with statement.
        """
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and log result.

        Args:
            exc_type: Exception type if raised.
            exc_val: Exception value if raised.
            exc_tb: Exception traceback if raised.
        """
        if self._start_time:
            self._duration_ms = (time.time() - self._start_time) * 1000

            if exc_type:
                self._logger.error(
                    f"Operation failed: {self._operation_name}",
                    duration_ms=self._duration_ms,
                    error=str(exc_val)
                )
            else:
                self._logger.debug(
                    f"Operation completed: {self._operation_name}",
                    duration_ms=self._duration_ms
                )

    @property
    def duration_ms(self) -> float:
        """Get operation duration in milliseconds.

        Returns:
            Duration in milliseconds, or 0 if still timing.
        """
        if not self._start_time:
            return 0
        if not self._duration_ms:
            return (time.time() - self._start_time) * 1000
        return self._duration_ms
