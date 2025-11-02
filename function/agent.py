"""NL2SQL Agent implementation with AgentOps monitoring."""

from __future__ import annotations

import logging
import os
from typing import Any

import agentops
from agentops.sdk.decorators import agent, operation
from langchain_community.llms import Ollama

from database import DatabaseManager

logger = logging.getLogger(__name__)


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


@agent
class NL2SQLAgent:
    """Natural Language to SQL conversion agent.

    Converts natural language queries to SQL, executes them against DuckDB,
    and formats results. Integrated with AgentOps for monitoring and tracing.
    """

    def __init__(self) -> None:
        """Initialize NL2SQL agent with database connection and LLM."""
        self.db_manager = DatabaseManager()
        self.llm = self._initialize_llm()

        agentops_key = os.getenv("AGENTOPS_API_KEY")
        if agentops_key:
            logger.info("Initializing AgentOps monitoring")
            agentops.init(
                api_key=agentops_key,
                api_endpoint=os.getenv("AGENTOPS_API_ENDPOINT", "https://api.agentops.ai"),
                default_tags=[" nl2sql", "duckdb"],
            )

    def _initialize_llm(self) -> Ollama:
        """Initialize Ollama LLM.

        Returns:
            Configured Ollama LLM instance.
        """
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M")

        logger.info(f"Initializing Ollama LLM: {model} at {base_url}")
        return Ollama(
            base_url=base_url,
            model=model,
            temperature=0.0,
        )

    @operation
    def _generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question.

        Args:
            question: Natural language question in Japanese.

        Returns:
            Generated SQL query string.

        Raises:
            ValueError: If generated SQL is empty or invalid.
        """
        if not question:
            raise ValueError("Question cannot be empty")

        prompt = SQL_GENERATION_PROMPT.format(question=question)
        logger.debug(f"Generating SQL for question: {question}")

        sql = self.llm.invoke(prompt)

        sql = sql.strip()
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()

        if not sql:
            raise ValueError("Failed to generate valid SQL")

        logger.info(f"Generated SQL: {sql}")
        return sql

    @operation
    def process_query(self, user_input: str) -> dict[str, Any]:
        """Process natural language query and return SQL results.

        Args:
            user_input: Natural language question from user.

        Returns:
            Dictionary containing:
                - success: Whether query succeeded
                - output: Formatted result text
                - sql: Generated SQL query
                - data: Raw query results
                - input: Original user input
                - error: Error message (only if success=False)
        """
        if not user_input:
            return {
                "success": False,
                "error": "User input cannot be empty",
                "input": user_input,
            }

        logger.info(f"Processing query: {user_input}")

        try:
            sql = self._generate_sql(user_input)
            result = self.db_manager.execute_query(sql)

            if not result:
                logger.warning("Query returned no results")
                return {
                    "success": True,
                    "output": "クエリは成功しましたが、結果はありませんでした。",
                    "sql": sql,
                    "data": [],
                    "input": user_input,
                }

            output = self._format_result(result)
            logger.info(f"Query processed successfully, returned {len(result)} rows")

            return {
                "success": True,
                "output": output,
                "sql": sql,
                "data": result,
                "input": user_input,
            }
        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "input": user_input,
            }

    def _format_result(self, result: list[dict[str, Any]]) -> str:
        """Format query result as human-readable text.

        Args:
            result: List of dictionaries containing query results.

        Returns:
            Formatted result string in Japanese.
        """
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

    @operation
    def get_schema_info(self) -> dict[str, Any]:
        """Get database schema information.

        Returns:
            Dictionary containing:
                - tables: List of table information dicts with name, columns, row_count
        """
        logger.info("Fetching database schema information")
        schema = self.db_manager.get_schema()

        tables: list[dict[str, Any]] = []
        current_table: dict[str, Any] | None = None

        for line in schema.split("\n"):
            if line.startswith("Table:"):
                current_table = {"name": line.split(":")[1].strip(), "columns": []}
                tables.append(current_table)
            elif line.strip() and ":" in line and current_table is not None:
                parts = line.strip().split(":", 1)
                if len(parts) == 2:
                    col_name, col_type = parts
                    current_table["columns"].append({
                        "name": col_name.strip(),
                        "type": col_type.strip(),
                    })

        for table in tables:
            try:
                query = f"SELECT COUNT(*) as count FROM {table['name']}"
                result = self.db_manager.execute_query(query)
                table["row_count"] = result[0]["count"] if result else 0
            except Exception as e:
                logger.warning(f"Failed to get row count for table {table['name']}: {e}")
                table["row_count"] = 0

        logger.info(f"Retrieved schema for {len(tables)} tables")
        return {"tables": tables}

