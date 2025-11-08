"""Multi-agent system using AG2 (AutoGen) framework with Phoenix tracing.

This module implements autonomous agents for database queries, web search,
and predictive reasoning using AG2's conversational multi-agent pattern.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from autogen.coding import LocalCommandLineCodeExecutor

from mcp_tools.database import create_database_tools
from mcp_tools.web import create_web_tools
from mcp_tools.interpreter import create_interpreter_tool

logger = logging.getLogger(__name__)


class AgentConfig:
    """Configuration for AG2 agents."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        """Initialize agent configuration.

        Args:
            model: LLM model name.
            base_url: Ollama API endpoint.
            temperature: LLM temperature for reproducibility.
        """
        model = model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M")
        base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

        self.llm_config = {
            "config_list": [
                {
                    "model": model,
                    "base_url": base_url,
                    "api_key": "ollama",
                }
            ],
            "temperature": temperature,
        }


def create_sql_agent(config: AgentConfig) -> AssistantAgent:
    """Create database specialist agent.

    Args:
        config: Agent configuration.

    Returns:
        Configured SQL specialist agent.
    """
    db_tools = create_database_tools()

    agent = AssistantAgent(
        name="sql_specialist",
        system_message="""You are a SQL database expert for a Japanese e-commerce system.

CRITICAL: You MUST call these functions to answer queries. DO NOT generate SQL in text.

Available functions:
1. get_database_schema() - ALWAYS call this first to see table structures
2. execute_sql_query(sql="YOUR_SQL") - Execute SQL and get results

MANDATORY WORKFLOW:
Step 1: Call get_database_schema() to see available tables
Step 2: Write correct SQL for the user's question
Step 3: Call execute_sql_query(sql="YOUR_SQL") with your SQL
Step 4: Explain results in Japanese
Step 5: Reply with "TERMINATE"

Example for "顧客数を教えて":
1. Call: get_database_schema()
2. See customers table exists
3. Call: execute_sql_query(sql="SELECT COUNT(*) FROM customers")
4. Say: "顧客数は200人です。TERMINATE"

NEVER write SQL in code blocks. ALWAYS use execute_sql_query() function.""",
        llm_config=config.llm_config,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    )

    for name, func in db_tools.items():
        agent.register_function(
            function_map={name: func}
        )

    return agent


def create_web_agent(config: AgentConfig) -> AssistantAgent:
    """Create web search and information gathering agent.

    Args:
        config: Agent configuration.

    Returns:
        Configured web research agent.
    """
    web_tools = create_web_tools()

    tool_descriptions = "\n".join([
        f"- {name}: {func.__doc__.split('.')[0] if func.__doc__ else 'No description'}"
        for name, func in web_tools.items()
    ])

    agent = AssistantAgent(
        name="web_researcher",
        system_message=f"""You are a web research specialist.

Available tools:
{tool_descriptions}

Your role:
1. Search web for current information and trends
2. Scrape relevant webpages for detailed data
3. Provide context from latest sources
4. Summarize findings clearly in Japanese

Important: When you have completed the task, respond with "TERMINATE" to end the conversation.
Focus on factual, recent information.""",
        llm_config=config.llm_config,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    )

    for name, func in web_tools.items():
        agent.register_function(
            function_map={name: func}
        )

    return agent


def create_reasoning_agent(config: AgentConfig, work_dir: Path) -> AssistantAgent:
    """Create data analysis and prediction agent with code execution.

    Args:
        config: Agent configuration.
        work_dir: Working directory for code execution.

    Returns:
        Configured reasoning agent with code interpreter.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    executor = LocalCommandLineCodeExecutor(work_dir=str(work_dir))

    interpreter_tools = create_interpreter_tool()

    agent = AssistantAgent(
        name="data_analyst",
        system_message="""You are a data analysis and prediction specialist.

Your role:
1. Analyze data provided by other agents
2. Write Python code for statistical analysis and predictions
3. Execute code safely and interpret results
4. Provide actionable insights in Japanese

Use only allowed libraries: math, statistics, datetime, json, re
Important: When you have completed the task, respond with "TERMINATE" to end the conversation.
Always explain your reasoning and methodology.""",
        llm_config=config.llm_config,
        code_execution_config={"executor": executor},
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    )

    for name, func in interpreter_tools.items():
        agent.register_function(
            function_map={name: func}
        )

    return agent


class MultiAgentOrchestrator:
    """Orchestrates multi-agent collaboration using AG2 GroupChat."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        work_dir: Path | None = None,
    ) -> None:
        """Initialize orchestrator with specialized agents.

        Args:
            model: LLM model name.
            base_url: Ollama API endpoint.
            work_dir: Working directory for code execution.
        """
        config = AgentConfig(model, base_url)
        work_dir = work_dir or Path("/tmp/ag2_workspace")

        self.sql_agent = create_sql_agent(config)
        self.web_agent = create_web_agent(config)
        self.reasoning_agent = create_reasoning_agent(config, work_dir)

        self.user_proxy = UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        )

        self.group_chat = GroupChat(
            agents=[
                self.user_proxy,
                self.sql_agent,
                self.web_agent,
                self.reasoning_agent,
            ],
            messages=[],
            max_round=10,
            speaker_selection_method="auto",
        )

        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=config.llm_config,
        )

    def execute(self, query: str) -> dict[str, Any]:
        """Execute query using multi-agent collaboration.

        Args:
            query: User query requiring multi-agent collaboration.

        Returns:
            Execution result with conversation history.

        Examples:
            >>> orchestrator = MultiAgentOrchestrator()
            >>> result = orchestrator.execute("Predict tomorrow's sales")
            >>> print(result["output"])
        """
        logger.info(f"Executing query: {query}")

        try:
            # Clear previous group chat messages
            self.group_chat.messages.clear()

            self.user_proxy.initiate_chat(
                self.manager,
                message=query,
            )

            # Extract conversation from manager's chat history
            # Manager stores messages with all agents, find user agent conversation
            conversation = []
            if hasattr(self.manager, 'chat_messages'):
                for agent, messages in self.manager.chat_messages.items():
                    if hasattr(agent, 'name') and agent.name == "user":
                        conversation = messages
                        break

            # Extract final meaningful message (skip empty and user messages)
            final_message = ""
            for msg in reversed(conversation):
                content = msg.get("content", "").strip()
                name = msg.get("name", "")
                if content and name not in ["user", "chat_manager", ""]:
                    final_message = content
                    break

            # Get unique agents (excluding system agents)
            agents = list(set(
                msg.get("name", "")
                for msg in conversation
                if msg.get("name") not in ["user", "chat_manager", ""]
            ))

            return {
                "success": True,
                "output": final_message,
                "conversation": conversation,
                "agents_involved": agents,
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
            }


def main() -> None:
    """Run example multi-agent scenario."""
    orchestrator = MultiAgentOrchestrator()

    queries = [
        "顧客数を教えて",
        "最新のEコマーストレンドを調査して",
        "今日の売上データから明日の売上を予測して",
    ]

    for query in queries:
        result = orchestrator.execute(query)
        logger.info(f"Query: {query}")
        logger.info(f"Result: {result['output']}")
        logger.info(f"Agents: {result.get('agents_involved', [])}")
        logger.info("-" * 80)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
