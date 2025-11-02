"""Database tools for AG2 agents via MCP protocol."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

import httpx


def create_database_tools(
    mcp_url: str | None = None,
    db_path: str | None = None,
) -> dict[str, Callable]:
    """Create database operation tools using MCP server.

    Args:
        mcp_url: MCP server URL (e.g., http://mcp-server:8080/mcp).
        db_path: Fallback to direct DuckDB if MCP unavailable.

    Returns:
        Dictionary mapping tool names to callable functions.
    """
    mcp_url = mcp_url or os.getenv("MCP_SERVER_URL", "http://mcp-server:8080/mcp")
    use_mcp = os.getenv("USE_MCP", "true").lower() == "true"

    db_path = db_path or os.getenv(
        "DATABASE_PATH",
        str(Path(__file__).parent.parent.parent / "data" / "ecommerce.db")
    )

    def _call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call MCP server tool via HTTP."""
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
            response = httpx.post(mcp_url, json=request, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise RuntimeError(f"MCP error: {result['error']}")

            return result.get("result")

        except Exception as e:
            raise RuntimeError(f"MCP call failed: {e}")

    def _fallback_direct_query(sql: str) -> list[dict[str, Any]]:
        """Fallback to direct DuckDB query."""
        import duckdb

        conn = duckdb.connect(db_path, read_only=True)
        try:
            result = conn.execute(sql).fetchall()
            headers = [desc[0] for desc in conn.description] if conn.description else []

            rows = []
            for row in result:
                row_dict = {headers[i]: row[i] for i in range(len(headers))}
                rows.append(row_dict)
            return rows
        finally:
            conn.close()

    def get_database_schema(query: str = "") -> str:
        """Get complete database schema with table structures and row counts.

        This function returns information about all tables in the database,
        including column names, types, and total row counts.
        Call this FIRST before writing any SQL queries.

        Args:
            query: Optional table name filter (unused but required for tool signature).

        Returns:
            Formatted schema information showing:
            - Table names
            - Column names and data types
            - Total number of rows in each table

        Example output:
            -- Table: customers
              customer_id (INTEGER)
              name (VARCHAR)
              email (VARCHAR)
              -- Total rows: 200
        """
        schema_query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
        """

        try:
            result = _call_mcp_tool("query", {"query": schema_query})

            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                    import json
                    rows = json.loads(content[0]["text"])
                    return _format_schema_from_rows(rows)

            return "Failed to retrieve schema"

        except Exception:
            rows = _fallback_direct_query(schema_query)
            return _format_schema_from_rows(rows)

    def _format_schema_from_rows(rows: list[dict[str, Any]]) -> str:
        """Format schema rows into readable text."""
        if not rows:
            return "No tables found"

        schema_info = []
        current_table = None

        for row in rows:
            table_name = row.get("table_name", "")
            column_name = row.get("column_name", "")
            data_type = row.get("data_type", "")

            if table_name != current_table:
                if current_table is not None:
                    try:
                        count_query = f"SELECT COUNT(*) as count FROM {current_table}"
                        count_result = _call_mcp_tool("query", {"query": count_query})

                        if isinstance(count_result, dict) and "content" in count_result:
                            content = count_result["content"]
                            if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                                import json
                                count_data = json.loads(content[0]["text"])
                                if count_data:
                                    count = count_data[0].get("count", 0)
                                    schema_info.append(f"  -- Total rows: {count}")
                    except Exception:
                        pass

                current_table = table_name
                schema_info.append(f"\n-- Table: {table_name}")

            schema_info.append(f"  {column_name} ({data_type})")

        if current_table:
            try:
                count_query = f"SELECT COUNT(*) as count FROM {current_table}"
                count_result = _call_mcp_tool("query", {"query": count_query})

                if isinstance(count_result, dict) and "content" in count_result:
                    content = count_result["content"]
                    if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                        import json
                        count_data = json.loads(content[0]["text"])
                        if count_data:
                            count = count_data[0].get("count", 0)
                            schema_info.append(f"  -- Total rows: {count}")
            except Exception:
                pass

        return "\n".join(schema_info)

    def execute_sql_query(sql: str) -> str:
        """Execute SQL query against the database and return formatted results.

        Use this function to run SELECT, COUNT, JOIN, and other SQL queries.
        The database is read-only for safety.
        Results are limited to 50 rows maximum.

        Args:
            sql: Valid SQL query string (e.g., "SELECT * FROM customers LIMIT 10")

        Returns:
            Formatted table with query results showing:
            - Column headers
            - Data rows (max 50)
            - Total row count if more than 50

        Example:
            Input: "SELECT COUNT(*) FROM customers"
            Output: "COUNT(*) | 200"

        Errors:
            Returns error message if SQL is invalid or table doesn't exist.
        """
        try:
            result = _call_mcp_tool("query", {"query": sql})

            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                    import json
                    rows = json.loads(content[0]["text"])
                    return _format_query_results(rows)

            return "Query failed"

        except Exception as e:
            try:
                rows = _fallback_direct_query(sql)
                return _format_query_results(rows)
            except Exception:
                return f"SQL Error: {e!s}"

    def _format_query_results(rows: list[dict[str, Any]]) -> str:
        """Format query results into readable table."""
        if not rows:
            return "Query returned no results."

        headers = list(rows[0].keys())
        output = [" | ".join(headers)]
        output.append("-" * len(output[0]))

        for row in rows[:50]:
            output.append(" | ".join(str(row.get(h, "")) for h in headers))

        if len(rows) > 50:
            output.append(f"\n... ({len(rows) - 50} more rows)")

        return "\n".join(output)

    return {
        "get_database_schema": get_database_schema,
        "execute_sql_query": execute_sql_query,
    }
