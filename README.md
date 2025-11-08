# NL2SQL Agent with AG2 Multi-Agent System + MCP

Natural Language to SQL conversion system with autonomous multi-agent collaboration powered by AG2 (AutoGen) and Model Context Protocol (MCP).

## Features

- 🤖 **Multi-Agent Collaboration**: Three specialized AI agents working together
  - **SQL Specialist**: Database schema analysis and SQL query generation via MCP
  - **Web Researcher**: Real-time web search and information gathering
  - **Data Analyst**: Statistical analysis and predictions with code execution
- 🔧 **MCP Integration**: Standardized Model Context Protocol for tool communication
- 🗣️ **Natural Language Interface**: Query databases using Japanese natural language
- 🚀 **High Performance**: DuckDB for sub-100ms query execution
- 📊 **Full Observability**: Phoenix (Arize AI) for automatic LLM tracing
- 💬 **Interactive UI**: Streamlit for intuitive multi-agent conversation
- 🇯🇵 **Japanese Optimized**: LLM fine-tuned for Japanese e-commerce queries

## Quick Start

```bash
# Clone and setup
git clone https://github.com/michiroooo/nl2sql-agent.git
cd nl2sql-agent

# Generate sample database
cd data && pip install -r requirements.txt && python setup_database.py && cd ..

# Start all services (Streamlit, Phoenix, Ollama, MCP Server)
docker compose -f docker-compose-ag2.yml up -d --build

# Download LLM model
docker exec nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Verify services
curl http://localhost:8080/health  # MCP Server
curl http://localhost:6006         # Phoenix
curl http://localhost:8501         # Streamlit

# Access UI at http://localhost:8501
```

## Architecture

```text
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│  Streamlit UI   │
│   (Port 8501)   │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────┐
│   MultiAgentOrchestrator (AG2)     │
│  ┌──────────┬──────────┬─────────┐ │
│  │SQL Agent │Web Agent │ Reasoning│ │
│  │          │          │ Agent    │ │
│  └────┬─────┴──────────┴─────────┘ │
└───────┼────────────────────────────┘
        │
        ▼
┌────────────────────┐
│    MCP Tools       │
│  (HTTP Client)     │
└─────────┬──────────┘
          │ HTTP JSON-RPC
          ▼
┌─────────────────────┐
│   MCP Server        │
│   (FastAPI)         │
│   Port 8080         │
└──────────┬──────────┘
           │
           ▼
     ┌─────────┐
     │ DuckDB  │
     └─────────┘

[All components traced by Phoenix on Port 6006]
```

**詳細**: [docs/architecture.md](docs/architecture.md)

## MCP Integration

This system implements the **Model Context Protocol (MCP)** for standardized tool communication between agents and external systems.

### Architecture Benefits

- ✅ **Standardized Interface**: JSON-RPC protocol for all tool calls
- ✅ **Separation of Concerns**: Agents focus on reasoning, MCP handles execution
- ✅ **Better Observability**: All tool calls logged and traceable
- ✅ **Flexible Deployment**: MCP server can scale independently
- ✅ **Fallback Support**: Direct DuckDB access if MCP unavailable

### MCP Server

The FastAPI-based MCP server provides:

- **Endpoint**: `http://mcp-server:8080/mcp`
- **Protocol**: JSON-RPC 2.0
- **Tools**: Database query execution via `query` tool
- **Health Check**: `http://mcp-server:8080/health`

Example MCP request:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query",
    "arguments": {
      "query": "SELECT COUNT(*) FROM customers"
    }
  }
}
```

## Usage Examples

### Database Query

```text
User: "2024年で最も売れた商品は？"
→ SQL Agent calls get_database_schema() via MCP
→ Analyzes schema and generates SQL
→ Calls execute_sql_query() via MCP
→ Returns formatted result
```

### Web Research

```text
User: "最新のEコマーストレンドを調査して"
→ Web Agent searches DuckDuckGo
→ Scrapes relevant content
→ Summarizes findings
```

### Data Analysis

```text
User: "明日の売上を予測して"
→ SQL Agent retrieves historical data via MCP
→ Reasoning Agent performs statistical analysis
→ Returns prediction with confidence interval
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b-instruct-q4_K_M` | LLM model |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama endpoint (Docker) / `http://localhost:11434` (local) |
| `DATABASE_PATH` | `/app/data/ecommerce.db` | DuckDB path |
| `PHOENIX_COLLECTOR_ENDPOINT` | `http://phoenix:4317` | Phoenix OTLP gRPC endpoint (use `http://localhost:4317` for local development) |
| `MCP_SERVER_URL` | `http://mcp-server:8080/mcp` | MCP server endpoint |
| `USE_MCP` | `true` | Enable MCP for database operations |

### Agent Settings

Edit `function/ag2_orchestrator.py`:

```python
# Max conversation rounds
max_round=10  # Increase for complex queries

# LLM temperature
temperature=0.0  # 0.0=deterministic, 1.0=creative
```

## Troubleshooting

### MCP Server Issues

Check MCP server health:

```bash
curl http://localhost:8080/health
docker logs nl2sql-mcp-server --tail 50
```

Test MCP query directly:

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "query",
      "arguments": {"query": "SELECT COUNT(*) FROM customers"}
    }
  }'
```

### Agents Not Responding

Check Ollama:

```bash
docker logs nl2sql-ollama --tail 50
docker exec nl2sql-ollama ollama list
```

Ensure model is downloaded:

```bash
docker exec nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M
```

### Environment Variables Not Set

Verify in container:

```bash
docker exec nl2sql-streamlit env | grep -E "MCP|OLLAMA|DATABASE"
```

### Database Not Found

Generate sample database:

```bash
cd data && python setup_database.py
```

### Container Restart

Restart all services:

```bash
docker compose -f docker-compose-ag2.yml down
docker compose -f docker-compose-ag2.yml up -d --build
```

## Observability

### Phoenix Tracing

Phoenix automatically traces all LLM calls, agent interactions, and MCP tool calls with zero configuration.

**Access**: <http://localhost:6006>

**Features**:

- Automatic instrumentation (no decorators needed)
- Real-time trace visualization
- Agent conversation flow tracking
- LLM call details (tokens, latency, costs)
- MCP tool execution tracking with request/response logs
- Error detection and debugging

**No Setup Required**: Traces appear automatically after executing queries in the Streamlit UI.

### MCP Observability

All MCP tool calls are logged:

```bash
# View MCP server logs
docker logs nl2sql-mcp-server -f

# Example output:
# INFO: 172.18.0.5:43222 - "POST /mcp HTTP/1.1" 200 OK
```

## Performance

**Benchmarks** (Apple M4 Max, 128GB RAM):

| Query Type | Agent | Time | Tokens | MCP Overhead |
|------------|-------|------|--------|--------------|
| Simple SQL | SQL | 2-5s | ~500 | <100ms |
| Web Search | Web | 5-10s | ~800 | N/A |
| Analysis | Multi | 15-30s | ~2000 | <100ms |

**Optimization Tips**:

- MCP server adds minimal latency (<100ms per call)
- Reduce `max_round` for simple queries
- Use smaller model for faster responses (trade-off: lower accuracy)
- Limit tool result sizes in MCP server
- Enable LLM response caching

## Project Structure

```text
nl2sql-agent/
├── mcp_server/                   # NEW: MCP Server
│   ├── server.py                 #   FastAPI JSON-RPC server
│   ├── requirements.txt          #   MCP server dependencies
│   └── Dockerfile                #   MCP server container
├── function/
│   ├── ag2_orchestrator.py       # Multi-agent orchestration
│   └── mcp_tools/                # MCP tool implementations
│       ├── database.py           # DB tools with MCP HTTP client
│       ├── web.py                # Search/scrape tools
│       └── interpreter.py        # Safe Python execution
├── ui/
│   └── app.py                    # Streamlit interface with Phoenix
├── data/
│   ├── ecommerce.db              # Sample DuckDB database
│   └── setup_database.py         # Sample data generator
├── docs/
│   └── architecture.md           # Detailed architecture docs
├── docker-compose-ag2.yml        # 4 services: UI, Phoenix, Ollama, MCP
└── .env.example                  # Environment variables template
```

## Future Improvements & Known Limitations

### Planned Enhancements

- **BatchSpanProcessor**: Implement batch processing for Phoenix traces (currently using simple span processor)
  - Reduces network overhead in high-load scenarios
  - Better performance for production deployments

- **AG2 Message Retrieval Patterns**: Document AG2's `chat_messages` vs `group_chat.messages` behavior
  - Current implementation uses `manager.chat_messages[agent]` for reliable message extraction
  - May need updates with future AG2 releases

- **Cleanup Tasks**:
  - Remove debug scripts (`debug_messages.py`, `debug_all_messages.py`, `test_groupchat.py`) before production deployment
  - These are useful for development/troubleshooting only

### Performance Considerations

- **Model Selection**: Qwen 2.5 Coder 7B offers good balance; consider larger models for complex queries
- **MCP Latency**: HTTP JSON-RPC adds ~50-100ms per tool call (acceptable for most use cases)
- **DuckDB Performance**: Suitable for datasets <10GB; consider PostgreSQL for larger scale

## License

MIT License

## References

- [AG2 (AutoGen) Documentation](https://microsoft.github.io/autogen/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Phoenix (Arize AI) Documentation](https://docs.arize.com/phoenix)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Model Context Protocol](https://modelcontextprotocol.io)
