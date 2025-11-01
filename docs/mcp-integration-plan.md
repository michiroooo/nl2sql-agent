# MCP Integration Plan for NL2SQL Agent

## Overview

This document outlines the plan to refactor the NL2SQL agent to use the Model Context Protocol (MCP) for database schema discovery, eliminating hardcoded schema knowledge and achieving a generic, database-agnostic architecture.

## Current Architecture Issues

### Hardcoded Schema Problem

In `function/agent.py`, the SQL generation prompt contains hardcoded database schema:

```python
Database Schema:
- customers: customer_id (INTEGER), customer_name (VARCHAR), prefecture (VARCHAR), registration_date (DATE)
- products: product_id (INTEGER), product_name (VARCHAR), category (VARCHAR), price (INTEGER), stock_quantity (INTEGER)
- orders: order_id (INTEGER), customer_name (VARCHAR), product_id (INTEGER), quantity (INTEGER), order_date (DATE), total_amount (INTEGER)
```

**Problems:**
- Schema changes require code modification
- Cannot work with different databases without changing code
- Maintenance burden increases with schema complexity
- Not scalable for production use

## Solution: MCP Integration

### What is MCP?

Model Context Protocol (MCP) is an open standard that enables AI applications to connect to external systems through a unified interface. Think of it as a USB-C port for AI applications.

### Using MotherDuck MCP Server

Instead of building our own MCP server, we will use the **official MotherDuck MCP Server**, which:
- Supports both local DuckDB and cloud MotherDuck databases
- Provides a single `query` tool for SQL execution
- Handles schema introspection via standard SQL (`information_schema`)
- Is production-ready, well-maintained, and widely used

**Repository:** https://github.com/motherduckdb/mcp-server-motherduck

## Implementation Plan

### Architecture Changes

#### Before (Current)
```
Streamlit UI → NL2SQL Agent (hardcoded schema) → DuckDB
                    ↓
                  Ollama
```

#### After (MCP-based)
```
Streamlit UI → NL2SQL Agent → MCP Client → MotherDuck MCP Server → DuckDB
                    ↓
                  Ollama
```

### Phase 1: Add MotherDuck MCP Server to Docker Compose

**File:** `docker-compose.yml`

Add a new service:

```yaml
  mcp-duckdb:
    image: python:3.11-slim
    container_name: nl2sql-mcp-duckdb
    command: >
      bash -c "pip install mcp-server-motherduck &&
               uvx mcp-server-motherduck --transport stream --port 8002
               --db-path /app/data/ecommerce.db --read-only"
    ports:
      - "8002:8002"
    volumes:
      - ./data:/app/data
    networks:
      - nl2sql-network
    restart: unless-stopped
```

**Key Parameters:**
- `--transport stream`: HTTP-based transport for inter-service communication
- `--port 8002`: Expose MCP server on port 8002
- `--db-path /app/data/ecommerce.db`: Path to DuckDB file
- `--read-only`: Prevent accidental data modification

### Phase 2: Integrate Python MCP SDK

**File:** `function/requirements.txt`

Add MCP SDK:
```
mcp>=1.0.0
```

**File:** `function/mcp_client.py` (New)

Create an MCP client wrapper:

```python
"""MCP Client for database schema discovery and query execution."""

from __future__ import annotations

import asyncio
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPDatabaseClient:
    """MCP client for interacting with DuckDB via MotherDuck MCP Server."""

    def __init__(self, server_url: str = "http://mcp-duckdb:8002") -> None:
        self.server_url = server_url
        self._session: ClientSession | None = None

    async def _get_session(self) -> ClientSession:
        """Get or create MCP session."""
        if self._session is None:
            # For HTTP/SSE transport
            # Note: MCP SDK's HTTP client implementation may vary
            # This is a placeholder for the actual implementation
            pass
        return self._session

    async def get_schema(self) -> str:
        """Get database schema using MCP query tool."""
        session = await self._get_session()

        # Query to get all tables and columns
        schema_query = """
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
        """

        result = await session.call_tool("query", {"query": schema_query})
        return self._format_schema(result)

    async def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """Execute SQL query via MCP."""
        session = await self._get_session()
        result = await session.call_tool("query", {"query": sql})
        return result.content

    def _format_schema(self, raw_result: Any) -> str:
        """Format schema query results into human-readable text."""
        # Parse and format the schema results
        # Group by table, list columns with types
        pass

    async def close(self) -> None:
        """Close MCP session."""
        if self._session:
            await self._session.close()
            self._session = None
```

### Phase 3: Refactor agent.py

**Changes to `function/agent.py`:**

1. **Remove hardcoded schema from prompt**
2. **Add MCP-aware prompt** that instructs LLM to:
   - First query schema if needed
   - Then generate SQL based on actual schema
   - Use ReAct-style reasoning

3. **Implement dynamic schema retrieval**

```python
SQL_GENERATION_PROMPT = """You are a SQL query generator for a DuckDB database.

IMPORTANT: You do NOT have predefined knowledge of the database schema. You must first discover the schema before generating SQL queries.

Available Tools:
1. get_schema(): Retrieve the complete database schema (tables, columns, types)
2. execute_query(sql): Execute a SQL query

Workflow:
1. If you don't know the schema, call get_schema() first
2. Analyze the user's question
3. Generate a SQL query based on the actual schema
4. Return the SQL query

User Question: {question}

DuckDB SQL Rules:
1. For date comparisons: WHERE order_date >= '2024-01-01' (string format)
2. For year extraction: EXTRACT(YEAR FROM order_date) or strftime(order_date, '%Y')
3. Use proper JOIN conditions when combining tables
4. Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) appropriately
5. Return only SELECT queries (no INSERT/UPDATE/DELETE)
6. For top N results: ORDER BY ... LIMIT N

SQL Query:"""
```

4. **Modify process_query() method:**

```python
async def process_query(self, user_input: str) -> dict[str, Any]:
    """Process natural language query using MCP for schema discovery."""
    try:
        # Step 1: Get schema via MCP
        schema = await self.mcp_client.get_schema()

        # Step 2: Generate SQL with actual schema context
        prompt = SQL_GENERATION_PROMPT.format(
            question=user_input,
            schema=schema
        )
        sql = self._generate_sql(prompt)

        # Step 3: Execute via MCP
        result = await self.mcp_client.execute_query(sql)

        # Step 4: Format results
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
```

### Phase 4: Update Streamlit UI

**File:** `ui/app.py`

Update to handle async operations:

```python
import asyncio

@st.cache_resource
def get_agent():
    """Initialize and cache the agent."""
    return NL2SQLAgent()

if prompt := st.chat_input("質問を入力してください（例：顧客数を教えて）"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("処理中..."):
            agent = get_agent()
            # Run async process_query in sync context
            result = asyncio.run(agent.process_query(prompt))

            if result["success"]:
                response = result["output"]
                st.markdown(response)
                # ... rest of the code
```

### Phase 5: Testing and Validation

#### Test Cases

1. **Schema Discovery Test**
   - Verify MCP server returns correct schema
   - Check schema formatting is readable

2. **Query Generation Test**
   - Test existing queries still work
   - Verify SQL generation uses actual schema

3. **Genericity Test**
   - Modify database schema (add/remove columns)
   - Verify agent adapts without code changes

4. **Error Handling Test**
   - Test MCP server connection failures
   - Verify graceful degradation

#### Validation Queries

```python
TEST_QUERIES = [
    "顧客数を教えて",
    "2024年で最も売れた商品の名前と売上個数を教えて",
    "東京都在住の顧客数を教えて",
    "購入金額トップ3の顧客名と購入金額を教えて",
]
```

## Benefits of MCP Integration

### 1. **Database Agnostic**
- Works with any database without code changes
- Schema changes automatically reflected
- Easy to switch between databases

### 2. **Maintainability**
- No hardcoded schema in code
- Single source of truth (the database itself)
- Reduced maintenance burden

### 3. **Extensibility**
- Can easily add new MCP servers for other data sources
- Supports multiple databases simultaneously
- Future-proof architecture

### 4. **Production Ready**
- Uses battle-tested MotherDuck MCP Server
- Standard protocol with wide adoption
- Active community and support

## Migration Strategy

### Step 1: Parallel Operation
- Keep existing code functional
- Add MCP integration alongside
- Compare results for validation

### Step 2: Feature Flag
- Use environment variable to toggle MCP mode
- Allow gradual rollout

### Step 3: Full Migration
- Remove hardcoded schema
- Make MCP the default path
- Update documentation

## Rollback Plan

If MCP integration causes issues:

1. **Immediate Rollback:** Revert to `feature/streamlit-ui` branch
2. **Quick Fix:** Add feature flag to disable MCP mode
3. **Debug Mode:** Keep old code path for comparison

## Timeline Estimate

- **Phase 1 (Docker Compose):** 1 hour
- **Phase 2 (MCP SDK):** 2 hours
- **Phase 3 (Agent Refactor):** 3 hours
- **Phase 4 (UI Updates):** 1 hour
- **Phase 5 (Testing):** 2 hours

**Total:** ~9 hours of development

## Success Criteria

1. ✅ MCP Server successfully connects to DuckDB
2. ✅ Schema is retrieved dynamically via MCP
3. ✅ All existing test queries work correctly
4. ✅ No hardcoded schema in agent code
5. ✅ System adapts to schema changes automatically
6. ✅ Performance is comparable to current implementation

## References

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MotherDuck MCP Server](https://github.com/motherduckdb/mcp-server-motherduck)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [DuckDB Documentation](https://duckdb.org/docs/)

## Next Steps

1. Review and approve this plan
2. Create feature branch `feature/mcp-integration`
3. Implement Phase 1 (Docker Compose)
4. Continue with subsequent phases
5. Create PR for review
