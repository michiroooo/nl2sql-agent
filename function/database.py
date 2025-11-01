"""Database connection and schema management."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
from langchain_community.utilities import SQLDatabase


class DatabaseManager:
    """Manage DuckDB connection and provide SQLDatabase interface."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.getenv(
            "DATABASE_PATH",
            str(Path(__file__).parent.parent / "data" / "ecommerce.db")
        )
        self._conn = None
        self._sql_database = None

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get DuckDB connection."""
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path, read_only=True)
        return self._conn

    @property
    def sql_database(self) -> SQLDatabase:
        """Get LangChain SQLDatabase interface."""
        if self._sql_database is None:
            self._sql_database = SQLDatabase.from_uri(f"duckdb:///{self.db_path}")
        return self._sql_database

    def get_schema(self) -> str:
        """Get database schema information."""
        tables = self.connection.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        
        schema_info = []
        for (table_name,) in tables:
            columns = self.connection.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall()
            
            schema_info.append(f"\n-- Table: {table_name}")
            for col in columns:
                schema_info.append(f"  {col[1]} {col[2]}")
        
        return "\n".join(schema_info)

    def execute_query(self, query: str) -> list[dict]:
        """Execute SQL query and return results as list of dicts."""
        result = self.connection.execute(query).fetchdf()
        return result.to_dict(orient="records")

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
