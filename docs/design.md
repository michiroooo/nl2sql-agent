# NL2SQL Agent System Design Document

## 1. Overview

Natural language to SQL conversion system using Model Context Protocol (MCP) for autonomous database exploration with Streamlit UI and AgentOps monitoring.

### Architecture Goals

- Implement MCP server for standardized database access
- Enable LLM to autonomously explore database schema
- Use ReAct pattern for transparent agent reasoning
- Support Japanese natural language queries
- Maintain high performance with DuckDB

### Key Innovation: MCP Integration

This system uses Model Context Protocol (MCP) to provide LLMs with standardized tools for database interaction. Unlike traditional approaches where schema is hardcoded, the LLM autonomously:

1. Discovers database structure using `get_database_schema` tool
2. Generates appropriate SQL queries based on discovered schema
3. Executes queries using `execute_sql_query` tool
4. Formats results into natural language

## 2. Technology Stack

### Core Components

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Frontend | Streamlit | 1.39+ | Chat interface |
| LLM | Ollama (qwen2.5-coder:7b) | latest | Code-specialized model |
| Database | DuckDB | 1.4+ | High-speed SQL engine |
| MCP Server | FastAPI | 0.120+ | MCP-compatible JSON-RPC server |
| Agent Framework | LangChain | 1.0+ | Tool integration |
| Backend | Python 3.11 | 3.11+ | Agent logic |
| Monitoring | AgentOps | 0.4+ | Agent observability |
| Container | Docker Compose | latest | Service orchestration |

### Why qwen2.5-coder:7b?

- **Code-specialized model** optimized for SQL generation
- Excellent instruction following for structured outputs
- Compact 7B parameter size for fast inference
- Good balance of performance and resource usage

## 3. System Architecture

### High-Level Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                    Streamlit UI (8501)                       │
│                  User Interface Layer                        │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                  NL2SQL Agent (agent_react.py)               │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              ReAct Pattern Flow                        │  │
│  │                                                         │  │
│  │  1. Get Schema  → 2. Generate SQL →                   │  │
│  │  3. Execute Query → 4. Format Answer                  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  Tools: MCPToolFactory (mcp_tools.py)                       │
└────────────┬─────────────────────────┬──────────────────────┘
             │                         │
             ▼                         ▼
┌────────────────────────┐  ┌──────────────────────────────┐
│  MCP Server (8080)     │  │    Ollama LLM (11434)        │
│  FastAPI JSON-RPC      │  │  qwen2.5-coder:7b            │
│                        │  │                              │
│  Tools:                │  │  Capabilities:               │
│  - get_database_schema │  │  - SQL generation            │
│  - execute_sql_query   │  │  - Response formatting       │
└────────┬───────────────┘  └──────────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   DuckDB Database       │
│   ecommerce.db          │
│                         │
│   Tables:               │
│   - customers (200)     │
│   - products (30)       │
│   - orders (1000)       │
└─────────────────────────┘
```

### Component Interactions

```text
User Query: "顧客数を教えて"
     │
     ▼
┌─────────────────────────────────────────────────┐
│ Step 1: Get Schema                              │
│ Agent → MCP Server → DuckDB                    │
│ Returns: Table/column information              │
└─────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│ Step 2: Generate SQL                            │
│ Agent → Ollama LLM                             │
│ Prompt: Schema + User Question                 │
│ Returns: SELECT COUNT(*) as count FROM customers│
└─────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│ Step 3: Execute Query                           │
│ Agent → MCP Server → DuckDB                    │
│ Returns: [{"count": 200}]                      │
└─────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│ Step 4: Format Answer                           │
│ Agent → Ollama LLM                             │
│ Prompt: Results + User Question                │
│ Returns: "データベースには200人の顧客がいます" │
└─────────────────────────────────────────────────┘
```

## 4. Database Schema

### Sample Data: Japanese E-commerce

```sql
-- Products table
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR,
    category VARCHAR,
    price INTEGER,
    stock_quantity INTEGER
);

-- Orders table
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_name VARCHAR,
    product_id INTEGER,
    quantity INTEGER,
    order_date DATE,
    total_amount INTEGER
);

-- Customers table
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name VARCHAR,
    prefecture VARCHAR,
    registration_date DATE
);
```

### Sample Data Content

Japanese retail scenario:

- **Products**: Electronics, books, groceries with Japanese names
- **Customers**: Japanese names with prefecture data
- **Orders**: Realistic transaction history spanning 2024

## 5. MCP Integration Details

### MCP Server Implementation

The custom MCP server (`mcp_server/server.py`) implements JSON-RPC 2.0 protocol:

```python
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query",
    "arguments": {
      "query": "SELECT * FROM customers LIMIT 5"
    }
  }
}
```

**Response Format**:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"customer_id\": 1, \"customer_name\": \"田中太郎\"}]"
      }
    ]
  },
  "error": null
}
```

### MCP Tools

#### 1. get_database_schema

**Purpose**: Retrieve complete database schema

**Implementation**:

```python
def get_schema_tool() -> Tool:
    def get_schema(_: str = "") -> str:
        schema_query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
        """
        result = _call_mcp_tool("query", {"query": schema_query})
        # Format as human-readable schema
        return formatted_schema

    return Tool(
        name="get_database_schema",
        description="Get complete database schema...",
        func=get_schema
    )
```

**Output Example**:

```text
Table: customers
  - customer_id (BIGINT)
  - customer_name (VARCHAR)
  - prefecture (VARCHAR)
  - registration_date (TIMESTAMP_NS)

Table: products
  - product_id (BIGINT)
  - product_name (VARCHAR)
  - category (VARCHAR)
  - price (BIGINT)
```

#### 2. execute_sql_query

**Purpose**: Execute SQL query and return results

**Implementation**:

```python
def query_tool() -> Tool:
    def execute_query(sql: str) -> str:
        result = _call_mcp_tool("query", {"query": sql})
        return result

    return Tool(
        name="execute_sql_query",
        description="Execute a SQL query...",
        func=execute_query
    )
```

**Input**: Valid DuckDB SQL SELECT query

**Output**: JSON array of results

### Agent Flow with MCP Tools

```python
class NL2SQLAgent:
    def process_query(self, user_input: str):
        # Step 1: Get schema
        schema_result = self.tools["get_database_schema"].invoke("")

        # Step 2: Generate SQL with LLM
        sql_query = self.llm.invoke(f"Schema: {schema_result}\nQ: {user_input}")

        # Step 3: Execute query
        query_result = self.tools["execute_sql_query"].invoke(sql_query)

        # Step 4: Format answer
        final_answer = self.llm.invoke(f"Results: {query_result}\nQ: {user_input}")

        return final_answer
```

## 6. Implementation Plan

### Phase 1: Infrastructure Setup ✅

- [x] Docker Compose configuration for all services
- [x] Streamlit UI deployment
- [x] DuckDB initialization with sample data
- [x] Network configuration between containers

### Phase 2: MCP Server Development ✅

- [x] Custom FastAPI MCP server
- [x] JSON-RPC 2.0 protocol implementation
- [x] Database query tool implementation
- [x] Error handling and validation

### Phase 3: Agent Implementation ✅

- [x] LangChain tool wrappers for MCP
- [x] Agent with tool invocation logic
- [x] Multi-step reasoning flow
- [x] AgentOps integration for monitoring

### Phase 4: Integration & Testing ✅

- [x] End-to-end query testing
- [x] Japanese language query validation
- [x] Error handling verification
- [x] UI integration with agent steps display

### Phase 5: Documentation ✅

- [x] API documentation
- [x] User guide for query patterns
- [x] Deployment instructions
- [x] Architecture documentation

## 6. Key Features

### Natural Language Query Examples

```
❌ Poor: "売上を見せて"
✅ Good: "2024年10月の商品カテゴリ別売上合計を教えて"

❌ Poor: "顧客データ"
✅ Good: "東京都在住の顧客で購入金額が10万円以上の人を抽出して"
```

### AgentOps Monitoring Points

1. Query input validation
2. SQL generation success/failure
3. Query execution time
4. Result formatting
5. Error tracking with context

### Security Considerations

- Read-only database access for agent
- SQL injection prevention via parameterized queries
- Input sanitization for natural language
- Rate limiting on API endpoints

## 7. File Structure

```
.
├── docker-compose.yml
├── function/
│   ├── Dockerfile
│   ├── main.py              # FastAPI app
│   ├── agent.py             # NL2SQL agent logic
│   ├── database.py          # DuckDB connection
│   └── requirements.txt
├── data/
│   ├── setup_database.py    # Sample data generator
│   └── sample_queries.md    # Example queries
├── docs/
│   └── design.md            # This document
└── README.md
```

## 8. Non-Functional Requirements

### Performance

- Query response time: < 3 seconds (95th percentile)
- Support concurrent users: 10+
- Database query execution: < 100ms

### Reliability

- Agent success rate: > 90%
- System uptime: > 99%
- Error recovery with fallback responses

### Maintainability

- Type-hinted Python code
- Comprehensive logging
- Unit test coverage: > 80%
- AgentOps metrics dashboard

## 9. Future Enhancements

- Multi-table JOIN query support
- Query result visualization (charts)
- Natural language result explanation
- Query history and favorites
- Custom domain vocabulary training
