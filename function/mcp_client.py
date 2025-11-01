"""MCP Client for database schema discovery and query execution."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any


class MCPDatabaseClient:
    """MCP client for interacting with DuckDB via MotherDuck MCP Server."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.getenv(
            "DATABASE_PATH",
            "/app/data/ecommerce.db"
        )
        self.read_only = os.getenv("MCP_READ_ONLY", "true").lower() == "true"
        self._mcp_command = self._build_mcp_command()

    def _build_mcp_command(self) -> list[str]:
        """Build MCP server command."""
        cmd = [
            "python",
            "-m",
            "mcp_server_motherduck",
            "--transport",
            "stdio",
            "--db-path",
            self.db_path,
        ]
        if self.read_only:
            cmd.append("--read-only")
        return cmd

    def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call MCP tool via subprocess."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        try:
            process = subprocess.Popen(
                self._mcp_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = process.communicate(input=json.dumps(request))

            if process.returncode != 0:
                raise RuntimeError(f"MCP server error: {stderr}")

            response = json.loads(stdout)
            if "error" in response:
                raise RuntimeError(f"MCP tool error: {response['error']}")

            return response.get("result")

        except Exception as e:
            raise RuntimeError(f"Failed to call MCP tool: {e}")

    def get_schema(self) -> str:
        """Get database schema using MCP query tool."""
        schema_query = """
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
        """

        result = self._call_mcp_tool("query", {"query": schema_query})
        return self._format_schema(result)

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """Execute SQL query via MCP."""
        result = self._call_mcp_tool("query", {"query": sql})

        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                if "text" in content[0]:
                    import json
                    return json.loads(content[0]["text"])
        return []

    def _format_schema(self, raw_result: Any) -> str:
        """Format schema query results into human-readable text."""
        if not raw_result or "content" not in raw_result:
            return "No schema information available"

        content = raw_result["content"]
        if not isinstance(content, list) or len(content) == 0:
            return "No schema information available"

        if "text" not in content[0]:
            return "Invalid schema format"

        try:
            rows = json.loads(content[0]["text"])
        except (json.JSONDecodeError, KeyError):
            return "Failed to parse schema"

        tables: dict[str, list[tuple[str, str]]] = {}
        for row in rows:
            table_name = row.get("table_name", "unknown")
            column_name = row.get("column_name", "unknown")
            data_type = row.get("data_type", "unknown")

            if table_name not in tables:
                tables[table_name] = []
            tables[table_name].append((column_name, data_type))

        schema_lines = []
        for table_name, columns in tables.items():
            schema_lines.append(f"Table: {table_name}")
            for col_name, col_type in columns:
                schema_lines.append(f"  {col_name}: {col_type}")

        return "\n".join(schema_lines)

    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a specific table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        if result and len(result) > 0:
            return result[0].get("count", 0)
        return 0
