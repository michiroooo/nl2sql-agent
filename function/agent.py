"""NL2SQL Agent implementation with AgentOps monitoring."""

from __future__ import annotations

import os
from typing import Any

import agentops
from langchain_community.llms import Ollama

from database import DatabaseManager


SQL_GENERATION_PROMPT = """You are a SQL query generator for a Japanese e-commerce database.

Database Schema:
- customers: customer_id, customer_name, prefecture, registration_date
- products: product_id, product_name, category, price, stock_quantity  
- orders: order_id, customer_name, product_id, quantity, order_date, total_amount

User Question: {question}

Generate ONLY a valid DuckDB SQL query to answer this question. Do not include explanations.
Rules:
1. Use proper JOIN conditions when combining tables
2. Use aggregate functions (COUNT, SUM, AVG) appropriately
3. Format dates as YYYY-MM-DD for comparisons
4. Return only SELECT queries (no INSERT/UPDATE/DELETE)

SQL Query:"""


class NL2SQLAgent:
    """Natural Language to SQL conversion agent."""

    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        self.llm = self._initialize_llm()
        
        agentops_key = os.getenv("AGENTOPS_API_KEY")
        if agentops_key:
            agentops.init(api_key=agentops_key)

    def _initialize_llm(self) -> Ollama:
        """Initialize Ollama LLM."""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "gemma2:2b-instruct-q4_K_M")
        
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

    @agentops.record_action("nl2sql_query")
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
            agentops.record_error(str(e))
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

