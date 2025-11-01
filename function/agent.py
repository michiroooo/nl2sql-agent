"""NL2SQL Agent implementation with AgentOps monitoring."""

from __future__ import annotations

import os
from typing import Any

import agentops
from langchain_community.llms import Ollama

from database import DatabaseManager
from mcp_client import MCPDatabaseClient


SQL_GENERATION_PROMPT = """You are a SQL query generator for a DuckDB database.

Database Schema:
{schema}

User Question: {question}

Generate ONLY a valid DuckDB SQL query to answer this question. Do not include explanations or markdown formatting.

IMPORTANT DuckDB SQL Rules:
1. For date comparisons, use: WHERE order_date >= '2024-01-01' (string format, not DATE() function)
2. For year extraction, use: EXTRACT(YEAR FROM order_date) or strftime(order_date, '%Y')
3. Use proper JOIN conditions when combining tables
4. Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) appropriately
5. Return only SELECT queries (no INSERT/UPDATE/DELETE)
6. For top N results, use: ORDER BY ... LIMIT N

Examples:
- "2024年の売上": WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
- "最も売れた商品": SELECT product_name, SUM(quantity) as total FROM orders JOIN products ... GROUP BY product_name ORDER BY total DESC LIMIT 1

SQL Query:"""


class NL2SQLAgent:
    """Natural Language to SQL conversion agent."""

    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        self.llm = self._initialize_llm()

        mcp_enabled = os.getenv("MCP_ENABLED", "false").lower() == "true"
        if mcp_enabled:
            try:
                self.mcp_client = MCPDatabaseClient(db_path="/app/data/ecommerce.db")
            except Exception:
                self.mcp_client = None
        else:
            self.mcp_client = None

        agentops_key = os.getenv("AGENTOPS_API_KEY")
        if agentops_key:
            try:
                agentops.init(api_key=agentops_key)
            except Exception:
                pass

    def _initialize_llm(self) -> Ollama:
        """Initialize Ollama LLM."""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M")

        return Ollama(
            base_url=base_url,
            model=model,
            temperature=0.0,
        )

    def _generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question."""
        if self.mcp_client:
            schema = self.mcp_client.get_schema()
        else:
            schema = self.db_manager.get_schema()

        prompt = SQL_GENERATION_PROMPT.format(schema=schema, question=question)
        sql = self.llm.invoke(prompt)

        sql = sql.strip()
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()

        return sql

    def process_query(self, user_input: str) -> dict[str, Any]:
        """Process natural language query and return SQL results."""
        try:
            sql = self._generate_sql(user_input)

            result = self.db_manager.execute_query(sql)

            if not result:
                return {
                    "success": True,
                    "output": "クエリは成功しましたが、結果はありませんでした。",
                    "sql": sql,
                    "data": [],
                }

            output = self._format_result(result)

            return {
                "success": True,
                "output": output,
                "sql": sql,
                "data": result,
                "input": user_input,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "input": user_input,
            }

    def _format_result(self, result: list[dict]) -> str:
        """Format query result as human-readable text."""
        if not result:
            return "結果はありませんでした。"

        if len(result) == 1 and len(result[0]) == 1:
            value = list(result[0].values())[0]
            return f"結果: {value}"

        lines = []
        for row in result[:5]:
            line = ", ".join(f"{k}: {v}" for k, v in row.items())
            lines.append(line)

        if len(result) > 5:
            lines.append(f"... および他 {len(result) - 5} 件")

        return "\n".join(lines)

    def get_schema_info(self) -> dict[str, Any]:
        """Get database schema information."""
        if self.mcp_client:
            schema_text = self.mcp_client.get_schema()
        else:
            schema_text = self.db_manager.get_schema()

        tables = []
        current_table = None

        for line in schema_text.split("\n"):
            line = line.strip()
            if line.startswith("Table:") or line.startswith("-- Table:"):
                if current_table:
                    tables.append(current_table)
                table_name = line.split(":")[-1].strip()
                current_table = {"name": table_name, "columns": []}
            elif line and current_table:
                parts = line.split()
                if len(parts) >= 2:
                    col_name = parts[0]
                    col_type = " ".join(parts[1:])
                    current_table["columns"].append({
                        "name": col_name,
                        "type": col_type
                    })

        if current_table:
            tables.append(current_table)

        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table['name']}"
            result = self.db_manager.execute_query(query)
            table["row_count"] = result[0]["count"] if result else 0

        return {"tables": tables}

