# NL2SQL Agent with MCP Integration

Natural Language to SQL conversion system using Model Context Protocol (MCP) with Streamlit UI and AgentOps monitoring.

## Features

- � **MCP Integration**: Autonomous database exploration using Model Context Protocol tools
- �🗣️ **Natural Language Interface**: Query databases using Japanese or English
- 🚀 **High Performance**: DuckDB for sub-100ms query execution
- 🔍 **AgentOps Monitoring**: Track agent behavior and performance
- 💬 **Chat Interface**: Streamlit for intuitive user experience
- 🇯🇵 **Japanese Support**: Optimized for Japanese e-commerce data
- 📊 **Data Visualization**: View SQL queries and results inline
- 🤖 **Autonomous Agent**: LLM explores schema and generates queries independently

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI (8501)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    NL2SQL Agent (ReAct)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Step 1: Get schema → Step 2: Generate SQL          │   │
│  │  Step 3: Execute query → Step 4: Format answer      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│   MCP Server (8080)     │  │    Ollama LLM (11434)        │
│  - get_database_schema  │  │  qwen2.5-coder:7b            │
│  - execute_sql_query    │  │                              │
└────────┬────────────────┘  └──────────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   DuckDB Database       │
│   ecommerce.db          │
└─────────────────────────┘
```

### Key Components

1. **Streamlit UI**: User-facing chat interface
2. **NL2SQL Agent**: Orchestrates tool usage and LLM interactions
3. **MCP Server**: Provides database access tools via JSON-RPC
4. **Ollama**: Local LLM for SQL generation and response formatting
5. **DuckDB**: High-performance analytical database

### How It Works

1. User submits natural language question
2. Agent calls `get_database_schema` MCP tool to explore database
3. LLM generates SQL query based on schema
4. Agent calls `execute_sql_query` MCP tool to run query
5. LLM formats results into natural language response

## Quick Start

### Prerequisites

- Docker and Docker Compose

### 1. Clone Repository

```bash
git clone https://github.com/michiroooo/nl2sql-agent.git
cd nl2sql-agent
```

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env to add your AgentOps API key (optional)
```

### 3. Generate Sample Database

```bash
cd data
pip install -r requirements.txt
python setup_database.py
cd ..
```

### 4. Start Services

```bash
docker compose up -d
```

### 5. Download Ollama Model

```bash
docker exec -it nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M
```

### 6. Access Streamlit UI

Open <http://localhost:8501> in your browser.

## Usage

### MCP Mode (Recommended)

The system uses MCP tools by default for autonomous database exploration:

**Japanese:**

```text
顧客数を教えて
2024年で最も売れた商品の名前と売上個数を教えて
東京都在住の顧客数を教えて
購入金額トップ3の顧客名と購入金額を教えて
```

**English:**

```text
Show me the number of customers
What product sold the most in 2024?
How many customers are from Tokyo?
Show top 3 customers by purchase amount
```

The agent will automatically:

1. Call `get_database_schema` to explore tables and columns
2. Generate appropriate SQL query
3. Execute query via `execute_sql_query`
4. Format results in natural language

### Viewing Agent Steps

Click "エージェントの思考過程" (Agent Thought Process) expander to see:

- **Step 1**: Database schema retrieval
- **Step 2**: SQL query generation
- **Step 3**: Query execution
- **Final Answer**: Natural language response

See `data/sample_queries.md` for more examples.

## Development

### Project Structure

```text
.
├── docker-compose.yml
├── ui/
│   ├── app.py            # Streamlit UI
│   ├── Dockerfile
│   └── requirements.txt
├── function/
│   ├── agent_react.py    # NL2SQL agent with MCP tools
│   ├── mcp_tools.py      # LangChain tool wrappers for MCP
│   ├── database.py       # DuckDB manager
│   └── requirements.txt
├── mcp_server/
│   ├── server.py         # Custom MCP server (FastAPI)
│   └── requirements.txt
├── data/
│   ├── setup_database.py # Sample data generator
│   └── ecommerce.db      # DuckDB database
└── docs/
    ├── design.md         # Design document
    └── mcp-integration-plan.md  # MCP integration details
```

### Local Development

```bash
# Install dependencies
cd function
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload --port 8001
```

### Database Schema

```sql
-- Customers
customer_id, customer_name, prefecture, registration_date

-- Products
product_id, product_name, category, price, stock_quantity

-- Orders
order_id, customer_name, product_id, quantity, order_date, total_amount
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTOPS_API_KEY` | AgentOps API key | (optional) |
| `DATABASE_PATH` | Path to DuckDB file | `/app/data/ecommerce.db` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://ollama:11434` |
| `OLLAMA_MODEL` | LLM model name | `qwen2.5-coder:7b-instruct-q4_K_M` |
| `MCP_ENABLED` | Enable MCP tools | `true` |
| `MCP_SERVER_URL` | MCP server endpoint | `http://mcp-duckdb:8080` |

## MCP Tools

The system provides two MCP tools for database interaction:

### get_database_schema

Returns complete database schema including tables, columns, and data types.

**Usage**: Agent calls this first to understand database structure

### execute_sql_query

Executes a SQL query and returns results in JSON format.

**Input**: Valid DuckDB SQL SELECT query

**Output**: Query results as JSON array

## Monitoring

If AgentOps API key is configured, visit <https://app.agentops.ai> to view:

- Query success/failure rates
- Response times
- Error tracking
- Agent execution traces

## Troubleshooting

### Ollama Connection Error

```bash
# Check Ollama is running
docker logs nl2sql-ollama

# Verify model is downloaded
docker exec -it nl2sql-ollama ollama list
```

### Database Not Found

```bash
# Regenerate database
cd data
python setup_database.py
```

### Open WebUI Not Accessible

```bash
# Check container status
docker-compose ps

# View logs
docker logs nl2sql-open-webui
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

## Links

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io)
- [AgentOps](https://agentops.ai)
- [DuckDB](https://duckdb.org)
- [Ollama](https://ollama.ai)
- [LangChain](https://langchain.com)
