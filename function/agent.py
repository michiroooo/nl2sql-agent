"""NL2SQL Agent implementation with AgentOps monitoring."""

from __future__ import annotations

import os
from typing import Any

import agentops
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.llms import Ollama

from database import DatabaseManager


AGENT_PROMPT = """You are a SQL expert assistant that helps users query a Japanese e-commerce database.

You have access to the following tables:
- customers: customer_id, customer_name, prefecture, registration_date
- products: product_id, product_name, category, price, stock_quantity
- orders: order_id, customer_name, product_id, quantity, order_date, total_amount

IMPORTANT RULES:
1. Generate SQL queries based on user's natural language questions
2. Always use proper JOIN conditions when combining tables
3. Return clear, formatted results
4. If the query is ambiguous, ask for clarification
5. Use aggregate functions (SUM, AVG, COUNT) appropriately
6. Format dates correctly for comparisons
7. Handle Japanese text properly in WHERE clauses

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""


class NL2SQLAgent:
    """Natural Language to SQL conversion agent."""

    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        self.llm = self._initialize_llm()
        self.agent = self._create_agent()
        
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

    def _create_agent(self) -> AgentExecutor:
        """Create LangChain SQL agent."""
        toolkit = SQLDatabaseToolkit(
            db=self.db_manager.sql_database,
            llm=self.llm
        )
        
        prompt = PromptTemplate.from_template(AGENT_PROMPT)
        
        agent = create_react_agent(
            llm=self.llm,
            tools=toolkit.get_tools(),
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=toolkit.get_tools(),
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    @agentops.record_action("nl2sql_query")
    def process_query(self, user_input: str) -> dict[str, Any]:
        """Process natural language query and return SQL results."""
        try:
            result = self.agent.invoke({"input": user_input})
            
            return {
                "success": True,
                "output": result.get("output", ""),
                "input": user_input,
            }
        except Exception as e:
            agentops.record_error(str(e))
            return {
                "success": False,
                "error": str(e),
                "input": user_input,
            }

    def get_schema_info(self) -> str:
        """Get database schema information."""
        return self.db_manager.get_schema()
