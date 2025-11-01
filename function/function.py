"""
title: NL2SQL Database Query Agent
author: michiroooo
version: 1.0.0
required_open_webui_version: 0.3.0
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import duckdb
from langchain_community.llms import Ollama
from pydantic import BaseModel, Field


SYSTEM_PROMPT = """あなたは日本のECサイトのデータベースを操作するSQLエキスパートです。

データベーススキーマ:
- customers: customer_id, customer_name, prefecture, registration_date
- products: product_id, product_name, category, price, stock_quantity
- orders: order_id, customer_name, product_id, quantity, order_date, total_amount

重要なルール:
1. 日本語の質問を理解し、適切なSQLクエリを生成する
2. JOINが必要な場合は適切な結合条件を使用する
3. 集計関数(SUM, COUNT, AVG等)を適切に使用する
4. 日付のフィルタリングには適切なフォーマットを使用する
5. 結果は分かりやすく整形する

質問に対して、まずSQLクエリを生成し、それを実行した結果を日本語で説明してください。
"""


class DatabaseManager:
    """Manage DuckDB connection."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or str(Path(__file__).parent.parent / "data" / "ecommerce.db")
        self._conn = None

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get DuckDB connection."""
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path, read_only=True)
        return self._conn

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
        """Execute SQL query and return results."""
        result = self.connection.execute(query).fetchdf()
        return result.to_dict(orient="records")

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


class NL2SQLAgent:
    """Natural Language to SQL conversion agent."""

    def __init__(
        self,
        database_path: str | None = None,
        ollama_base_url: str = "http://ollama:11434",
        ollama_model: str = "gemma2:2b-instruct-q4_K_M"
    ) -> None:
        self.db_manager = DatabaseManager(database_path)
        self.llm = Ollama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=0.0,
        )

    def _generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question."""
        schema_info = self.db_manager.get_schema()

        prompt = f"""{SYSTEM_PROMPT}

データベーススキーマ情報:
{schema_info}

質問: {question}

上記の質問に答えるためのSQLクエリを生成してください。
SQLクエリのみを返し、説明や追加のテキストは不要です。
クエリはSELECT文で始めてください。

SQL:"""

        sql = self.llm.invoke(prompt)

        # Clean up the response
        sql = str(sql).strip()
        if sql.startswith("```sql"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        elif sql.startswith("```"):
            sql = sql.replace("```", "").strip()

        # Extract only SELECT query
        if "SELECT" in sql.upper():
            sql_lines = sql.split("\n")
            sql = "\n".join([line for line in sql_lines if line.strip() and not line.strip().startswith("#")])

        return sql.strip()

    def process_query(self, user_input: str) -> dict[str, Any]:
        """Process natural language query and return SQL results."""
        try:
            sql_query = self._generate_sql(user_input)
            result = self.db_manager.execute_query(sql_query)

            if result:
                output = f"実行したSQL:\n{sql_query}\n\n結果:\n{result}"
            else:
                output = f"実行したSQL:\n{sql_query}\n\n結果: データが見つかりませんでした。"

            return {
                "success": True,
                "output": output,
                "sql": sql_query,
                "result": str(result),
                "input": user_input,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "input": user_input,
            }


class Pipe:
    """NL2SQL Query Pipeline for Open WebUI."""

    class Valves(BaseModel):
        """Configuration valves for the pipeline."""
        database_path: str = Field(
            default="/app/data/ecommerce.db",
            description="Path to the DuckDB database file"
        )
        ollama_base_url: str = Field(
            default="http://ollama:11434",
            description="Ollama API endpoint URL"
        )
        ollama_model: str = Field(
            default="gemma2:2b-instruct-q4_K_M",
            description="Ollama model name to use"
        )

    def __init__(self):
        """Initialize the pipeline."""
        self.type = "pipe"
        self.valves = self.Valves()
        self.agent = None

    def _ensure_agent(self):
        """Lazy initialization of agent with current valve settings."""
        if self.agent is None:
            self.agent = NL2SQLAgent(
                database_path=self.valves.database_path,
                ollama_base_url=self.valves.ollama_base_url,
                ollama_model=self.valves.ollama_model
            )

    def pipe(self, body: dict, __user__: Optional[dict] = None) -> str:
        """
        Process a natural language query and return SQL results.

        Args:
            body: Request body containing messages
            __user__: User information (optional)

        Returns:
            SQL query results as a formatted string
        """
        self._ensure_agent()

        # Extract the last user message
        messages = body.get("messages", [])
        if not messages:
            return "エラー: メッセージが見つかりません"

        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return "エラー: ユーザーメッセージが見つかりません"

        # Process the query
        result = self.agent.process_query(user_message)

        if result["success"]:
            return result["output"]
        else:
            return f"エラー: {result.get('error', '不明なエラーが発生しました')}"
