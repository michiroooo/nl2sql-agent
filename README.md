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

See full documentation: [docs/architecture.md](docs/architecture.md)

## License

MIT License
