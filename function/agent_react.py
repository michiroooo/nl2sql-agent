"""NL2SQL Agent implementation with MCP tools and simple chain pattern."""

from __future__ import annotations

import os
from typing import Any, NamedTuple

import agentops
from langchain_community.llms import Ollama

from database import DatabaseManager
from mcp_tools import MCPToolFactory


class AgentAction(NamedTuple):
    """Agent action structure for intermediate steps."""

    tool: str
    tool_input: Any


class NL2SQLAgent:
    """Natural Language to SQL conversion agent with MCP tools."""

    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        self.llm = self._initialize_llm()

        mcp_enabled = os.getenv("MCP_ENABLED", "false").lower() == "true"
        if mcp_enabled:
            try:
                mcp_factory = MCPToolFactory()
                self.tools = {
                    "get_database_schema": mcp_factory.get_schema_tool(),
                    "execute_sql_query": mcp_factory.query_tool(),
                }
                self.use_mcp = True
            except Exception as e:
                print(f"MCP initialization failed: {e}")
                self.use_mcp = False
                self.tools = {}
        else:
            self.use_mcp = False
            self.tools = {}

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

    def process_query(self, user_input: str) -> dict[str, Any]:
        """Process natural language query using MCP tools."""
        if not self.use_mcp or not self.tools:
            return {
                "success": False,
                "error": "MCP is not enabled or failed to initialize",
                "input": user_input,
            }

        intermediate_steps = []

        try:
            # Step 1: Get database schema
            schema_tool = self.tools["get_database_schema"]
            schema_result = schema_tool.invoke("")
            action = AgentAction(tool="get_database_schema", tool_input="")
            intermediate_steps.append((action, schema_result))

            # Step 2: Generate SQL query using LLM
            sql_prompt = f"""Based on the following database schema, generate a SQL query to answer the user's question.

Database Schema:
{schema_result}

User Question: {user_input}

Generate ONLY the SQL query, without any explanation or markdown formatting.
For DuckDB, use proper date functions like EXTRACT(YEAR FROM date_column) or strftime().
"""

            sql_query = self.llm.invoke(sql_prompt).strip()
            # Remove markdown code blocks if present
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            action = AgentAction(tool="generate_sql", tool_input=user_input)
            intermediate_steps.append((action, sql_query))

            # Step 3: Execute SQL query
            query_tool = self.tools["execute_sql_query"]
            query_result = query_tool.invoke(sql_query)
            action = AgentAction(tool="execute_sql_query", tool_input=sql_query)
            intermediate_steps.append((action, query_result))

            # Step 4: Format final answer
            answer_prompt = f"""Based on the SQL query results, provide a clear and natural answer to the user's question.

User Question: {user_input}
SQL Query: {sql_query}
Query Results: {query_result}

Provide a natural language answer:"""

            final_answer = self.llm.invoke(answer_prompt).strip()

            return {
                "success": True,
                "output": final_answer,
                "input": user_input,
                "intermediate_steps": intermediate_steps,
                "sql_query": sql_query,
                "query_results": query_result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "input": user_input,
                "intermediate_steps": intermediate_steps,
            }

    def get_schema_info(self) -> dict[str, Any]:
        """Get database schema information."""
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
