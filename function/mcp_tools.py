"""MCP Tools for LangChain integration."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from langchain_core.tools import Tool


class MCPToolFactory:
    """Factory for creating LangChain tools from MCP server."""

    def __init__(self, mcp_server_url: str | None = None) -> None:
        self.mcp_server_url = mcp_server_url or os.getenv(
            "MCP_SERVER_URL",
            "http://mcp-duckdb:8080"
        )

    def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call MCP tool via HTTP."""
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
            response = httpx.post(
                f"{self.mcp_server_url}/mcp",
                json=request,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result and result["error"] is not None:
                return f"Error: {result['error']}"

            mcp_result = result.get("result", {})

            if isinstance(mcp_result, dict) and "content" in mcp_result:
                content = mcp_result["content"]
                if isinstance(content, list) and len(content) > 0:
                    if "text" in content[0]:
                        return content[0]["text"]

            return json.dumps(mcp_result)

        except Exception as e:
            return f"Error calling MCP tool: {e}"

    def get_schema_tool(self) -> Tool:
        """Create a tool for getting database schema."""
        def get_schema(_: str = "") -> str:
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

            try:
                rows = json.loads(result)
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
                        schema_lines.append(f"  - {col_name} ({col_type})")
                    schema_lines.append("")

                return "\n".join(schema_lines)
            except Exception:
                return result

        return Tool(
            name="get_database_schema",
            description="Get the complete database schema including all tables and columns. Use this tool first to understand the database structure before writing queries.",
            func=get_schema
        )

    def query_tool(self) -> Tool:
        """Create a tool for executing SQL queries."""
        def execute_query(sql: str) -> str:
            result = self._call_mcp_tool("query", {"query": sql})
            return result

        return Tool(
            name="execute_sql_query",
            description="Execute a SQL query against the database. Input should be a valid DuckDB SQL SELECT query. Returns query results in JSON format.",
            func=execute_query
        )

    def get_all_tools(self) -> list[Tool]:
        """Get all available MCP tools."""
        return [
            self.get_schema_tool(),
            self.query_tool(),
        ]
