"""NL2SQL Agent implementation with AgentOps monitoring."""

from __future__ import annotations

import os
from typing import Any

import agentops
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase

from database import DatabaseManager


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
        model = os.getenv("OLLAMA_MODEL", "gemma2:9b-instruct-fp16")

        return Ollama(
            base_url=base_url,
            model=model,
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
            # Generate SQL query
            sql_query = self._generate_sql(user_input)

            # Execute SQL query
            result = self.db_manager.execute_query(sql_query)

            # Format result
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

    def get_schema_info(self) -> str:
        """Get database schema information."""
        return self.db_manager.get_schema()
