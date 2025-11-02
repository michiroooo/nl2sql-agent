"""Database tools for AG2 agents via MCP protocol."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import duckdb


def create_database_tools(db_path: str | None = None) -> dict[str, Callable]:
    """Create database operation tools.

    Args:
        db_path: Path to DuckDB database file.

    Returns:
        Dictionary mapping tool names to callable functions.
    """
    db_path = db_path or os.getenv(
        "DATABASE_PATH",
        str(Path(__file__).parent.parent.parent / "data" / "ecommerce.db")
    )

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
        conn = duckdb.connect(db_path, read_only=True)

        try:
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
            ).fetchall()

            schema_info = []
            for (table_name,) in tables:
                columns = conn.execute(
                    f"PRAGMA table_info('{table_name}')"
                ).fetchall()

                schema_info.append(f"\n-- Table: {table_name}")
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    schema_info.append(f"  {col_name} ({col_type})")

                row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                schema_info.append(f"  -- Total rows: {row_count}")

            return "\n".join(schema_info)

        finally:
            conn.close()

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
        conn = duckdb.connect(db_path, read_only=True)

        try:
            result = conn.execute(sql).fetchall()

            if not result:
                return "Query returned no results."

            headers = [desc[0] for desc in conn.description]

            output = [" | ".join(headers)]
            output.append("-" * len(output[0]))

            for row in result[:50]:
                output.append(" | ".join(str(val) for val in row))

            if len(result) > 50:
                output.append(f"\n... ({len(result) - 50} more rows)")

            return "\n".join(output)

        except Exception as e:
            return f"SQL Error: {e!s}"

        finally:
            conn.close()

    return {
        "get_database_schema": get_database_schema,
        "execute_sql_query": execute_sql_query,
    }
