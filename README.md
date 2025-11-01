# NL2SQL Agent with AG2 Multi-Agent System

Natural Language to SQL conversion system with autonomous multi-agent collaboration powered by AG2 (AutoGen).

## Features

- 🤖 **Multi-Agent Collaboration**: Three specialized AI agents working together
  - **SQL Specialist**: Database schema analysis and SQL query generation
  - **Web Researcher**: Real-time web search and information gathering
  - **Data Analyst**: Statistical analysis and predictions with code execution
- 🗣️ **Natural Language Interface**: Query databases using Japanese natural language
- 🚀 **High Performance**: DuckDB for sub-100ms query execution
- 📊 **Full Observability**: OpenTelemetry + ClickHouse for distributed tracing
- 💬 **Interactive UI**: Streamlit for intuitive multi-agent conversation
- 🇯🇵 **Japanese Optimized**: LLM fine-tuned for Japanese e-commerce queries

## Quick Start

```bash
# Clone and setup
git clone https://github.com/michiroooo/nl2sql-agent.git
cd nl2sql-agent

# Generate sample database
cd data && pip install -r requirements.txt && python setup_database.py && cd ..

# Start system
docker compose -f docker-compose-ag2.yml up -d

# Download model
docker exec nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Access UI at http://localhost:8501
```

## Architecture

```text
User Browser → Streamlit UI → MultiAgentOrchestrator → [SQL, Web, Reasoning] Agents
                                                      ↓
                                                  MCP Tools
                                                      ↓
                                         [DuckDB, Web, Interpreter]
```

**詳細**: [docs/architecture.md](docs/architecture.md)

## Usage Examples

### Database Query
```
User: "2024年で最も売れた商品は？"
→ SQL Agent analyzes schema → Generates SQL → Returns result
```

### Web Research
```
User: "最新のEコマーストレンドを調査して"
→ Web Agent searches DuckDuckGo → Scrapes content → Summarizes
```

### Data Analysis
```
User: "明日の売上を予測して"
→ SQL Agent gets historical data → Reasoning Agent runs analysis → Prediction
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b-instruct-q4_K_M` | LLM model |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama endpoint |
| `DATABASE_PATH` | `/app/data/ecommerce.db` | DuckDB path |

### Agent Settings

Edit `function/ag2_orchestrator.py`:

```python
# Max conversation rounds
max_round=10  # Increase for complex queries

# LLM temperature
temperature=0.0  # 0.0=deterministic, 1.0=creative
```

## Troubleshooting

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

### Import Errors

Check pyautogen version:
```bash
docker exec nl2sql-streamlit pip show pyautogen
# Expected: Version: 0.2.35 (not 0.10.0)
```

Rebuild if needed:
```bash
docker compose -f docker-compose-ag2.yml build --no-cache streamlit-ui
```

### Database Not Found

Generate database:
```bash
cd data && python setup_database.py
```

### Traces Not Appearing

Check OTel Collector:
```bash
docker logs nl2sql-otel-collector --tail 50
# Expected: "Everything is ready. Begin running and processing data."
```

Query ClickHouse:
```bash
docker exec nl2sql-clickhouse clickhouse-client --password password \
  --query "SELECT COUNT(*) FROM otel_2.otel_traces"
```

## Performance

**Benchmarks** (Apple M4 Max, 128GB RAM):

| Query Type | Agent | Time | Tokens |
|------------|-------|------|--------|
| Simple SQL | SQL | 2-5s | ~500 |
| Web Search | Web | 5-10s | ~800 |
| Analysis | Multi | 15-30s | ~2000 |

**Optimization Tips**:
- Reduce `max_round` for simple queries
- Use smaller model (gemma2:2b) for faster responses
- Limit tool result sizes
- Enable LLM response caching

## Project Structure

```text
nl2sql-agent/
├── function/
│   ├── ag2_orchestrator.py      # Multi-agent orchestration
│   ├── database.py               # DuckDB connection
│   └── mcp_tools/                # MCP tool implementations
│       ├── database.py           # DB schema/query tools
│       ├── web.py                # Search/scrape tools
│       └── interpreter.py        # Safe Python execution
├── ui/
│   └── app.py                    # Streamlit interface
├── data/
│   └── setup_database.py         # Sample data generator
├── docs/
│   └── architecture.md           # Detailed architecture docs
├── agentops/
│   ├── otel-collector-config.yaml
│   └── clickhouse/migrations/
└── docker-compose-ag2.yml        # Deployment config
```

## License

MIT License

## References

- [AG2 (AutoGen) Documentation](https://microsoft.github.io/autogen/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Streamlit Documentation](https://docs.streamlit.io/)
