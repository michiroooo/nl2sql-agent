"""NL2SQL Agent implementation with AgentOps monitoring."""

from __future__ import annotations

import os
from typing import Any

import agentops
from langchain_community.llms import Ollama

from database import DatabaseManager


SQL_GENERATION_PROMPT = """You are a SQL query generator for a Japanese e-commerce database using DuckDB.

Database Schema:
- customers: customer_id (INTEGER), customer_name (VARCHAR), prefecture (VARCHAR), registration_date (DATE)
- products: product_id (INTEGER), product_name (VARCHAR), category (VARCHAR), price (INTEGER), stock_quantity (INTEGER)
- orders: order_id (INTEGER), customer_name (VARCHAR), product_id (INTEGER), quantity (INTEGER), order_date (DATE), total_amount (INTEGER)

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
        prompt = SQL_GENERATION_PROMPT.format(question=question)
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
        schema = self.db_manager.get_schema()

        tables = []
        for line in schema.split("\n"):
            if line.startswith("Table:"):
                current_table = {"name": line.split(":")[1].strip(), "columns": []}
                tables.append(current_table)
            elif line.strip() and ":" in line and tables:
                col_name, col_type = line.strip().split(":")
                tables[-1]["columns"].append({
                    "name": col_name.strip(),
                    "type": col_type.strip()
                })

        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table['name']}"
            result = self.db_manager.execute_query(query)
            table["row_count"] = result[0]["count"] if result else 0

        return {"tables": tables}

