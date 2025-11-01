# NL2SQL Agent with AgentOps Self-Hosting

Natural Language to SQL conversion system with full AgentOps observability platform (self-hosted).

## Features

- 🗣️ **Natural Language Interface**: Query databases using Japanese or English
- 🚀 **High Performance**: DuckDB for sub-100ms query execution
- � **AgentOps Self-Hosted**: Full observability stack with traces, metrics, and analytics
- 💬 **Chat Interface**: Streamlit for intuitive user experience
- 🇯🇵 **Japanese Support**: Optimized for Japanese e-commerce data
- � **Distributed Tracing**: OpenTelemetry integration for end-to-end visibility

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
└──────────┬────────────────────────────────┬─────────────────┘
           │                                │
           │ Port 8501                      │ Port 3000
           ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐
│   Streamlit UI      │          │ AgentOps Dashboard  │
│  (Chat Interface)   │          │   (Next.js)         │
└──────────┬──────────┘          └──────────┬──────────┘
           │                                │
           │ @agent, @operation             │ API Calls
           ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐
│   NL2SQL Agent      │◄─────────┤  AgentOps API       │
│  (with decorators)  │ Track    │   (FastAPI)         │
└──────────┬──────────┘          └──────────┬──────────┘
           │                                │
           │ SQL Queries                    │ Store metadata
           ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐
│     DuckDB          │          │   PostgreSQL        │
│  (E-commerce Data)  │          │  (User/API Data)    │
└─────────────────────┘          └─────────────────────┘
           │
           │ Traces via OTLP
           ▼
┌─────────────────────┐
│  OTel Collector     │
│  (Port 4318)        │
└──────────┬──────────┘
           │
           │ Store traces
           ▼
┌─────────────────────┐
│    ClickHouse       │
│  (Traces & Metrics) │
└─────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available

### 1. Clone Repository

```bash
git clone https://github.com/michiroooo/nl2sql-agent.git
cd nl2sql-agent
```

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env and set a secure JWT_SECRET_KEY
```

**Required environment variables:**
- `JWT_SECRET_KEY`: Set a random 32+ character string for JWT signing
- `CLICKHOUSE_PASSWORD`: Password for ClickHouse (default: `password`)
- `POSTGRES_PASSWORD`: Password for PostgreSQL (default: `postgres`)

### 3. Generate Sample Database

```bash
cd data
pip install -r requirements.txt
python setup_database.py
cd ..
```

### 4. Start All Services

```bash
docker compose up -d
```

This will start:
- **Streamlit UI** (Port 8501) - Chat interface
- **AgentOps Dashboard** (Port 3000) - Observability dashboard
- **AgentOps API** (Port 8000) - Backend API
- **Ollama** (Port 11434) - LLM inference
- **ClickHouse** (Port 8123, 9000) - Trace storage
- **PostgreSQL** (Port 5432) - Metadata storage
- **OTel Collector** (Port 4317, 4318) - Trace collection

### 5. Download Ollama Model

```bash
docker exec -it nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M
```

### 6. Access Interfaces

- **Streamlit UI**: http://localhost:8501
- **AgentOps Dashboard**: http://localhost:3000
- **AgentOps API Docs**: http://localhost:8000/docs

## Usage

### Example Queries

**Japanese:**
```
顧客数を教えて
2024年で最も売れた商品の名前と売上個数を教えて
東京都在住の顧客数を教えて
購入金額トップ3の顧客名と購入金額を教えて
```

**English:**
```
Show me the number of customers
What product sold the most in 2024?
How many customers are from Tokyo?
Show top 3 customers by purchase amount
```

See `data/sample_queries.md` for more examples.

### Viewing Traces in AgentOps Dashboard

1. Open http://localhost:3000
2. Navigate to **Traces** section
3. View detailed execution traces with:
   - Operation timeline
   - SQL query generation steps
   - Database execution times
   - LLM prompts and responses
   - Error traces

## Development

### Project Structure

```
.
├── docker-compose.yml
├── agentops/
│   ├── otel-collector-config.yaml  # OTel configuration
│   └── clickhouse/
│       └── migrations/
│           └── 0000_init.sql       # ClickHouse schema
├── ui/
│   ├── app.py            # Streamlit UI
│   ├── Dockerfile
│   └── requirements.txt
├── function/
│   ├── agent.py          # NL2SQL agent (with @agent, @operation)
│   ├── database.py       # DuckDB manager
│   └── requirements.txt
├── data/
│   ├── setup_database.py # Sample data generator
│   └── ecommerce.db      # DuckDB database
└── docs/
    └── design.md         # Design document
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
| `AGENTOPS_API_KEY` | AgentOps API key (optional for self-hosted) | - |
| `AGENTOPS_API_ENDPOINT` | AgentOps API endpoint | `http://localhost:8000` |
| `AGENTOPS_EXPORTER_ENDPOINT` | OTLP exporter endpoint | `http://localhost:4318/v1/traces` |
| `DATABASE_PATH` | Path to DuckDB file | `/app/data/ecommerce.db` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://ollama:11434` |
| `OLLAMA_MODEL` | LLM model name | `qwen2.5-coder:7b-instruct-q4_K_M` |
| `JWT_SECRET_KEY` | JWT signing secret (32+ chars) | **Required** |
| `CLICKHOUSE_PASSWORD` | ClickHouse password | `password` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |

### AgentOps Decorators

The agent uses AgentOps decorators for automatic tracing:

```python
from agentops.sdk.decorators import agent, operation

@agent
class NL2SQLAgent:
    @operation
    def _generate_sql(self, question: str) -> str:
        # Automatically tracked
        pass
    
    @operation
    def process_query(self, user_input: str) -> dict:
        # Automatically tracked
        pass
```

## Monitoring & Observability

### Metrics Available

- **Query Performance**: End-to-end latency, SQL generation time, DB execution time
- **Success Rates**: Query success/failure rates, error types
- **LLM Usage**: Token counts, model performance, prompt effectiveness
- **System Health**: Database connection status, service availability

### Trace Details

Each query generates a trace with:
1. **Agent Span**: Overall query processing
2. **SQL Generation Operation**: LLM prompt and generated SQL
3. **Database Execution**: Query execution time and results
4. **Formatting**: Result formatting duration

## Troubleshooting

### Services Not Starting

```bash
# Check all container status
docker compose ps

# View logs for specific service
docker compose logs -f streamlit-ui
docker compose logs -f agentops-api
docker compose logs -f clickhouse
```

### ClickHouse Connection Error

```bash
# Verify ClickHouse is healthy
docker exec -it nl2sql-clickhouse clickhouse-client --query "SELECT 1"

# Check schema creation
docker exec -it nl2sql-clickhouse clickhouse-client --query "SHOW DATABASES"
```

### AgentOps Dashboard Not Loading

```bash
# Check API connectivity
curl http://localhost:8000/health

# Check dashboard logs
docker compose logs -f agentops-dashboard
```

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

## Performance Tips

1. **ClickHouse**: Traces are kept for 3 days (TTL). Adjust in migration SQL if needed.
2. **Memory**: Allocate at least 4GB RAM for all services.
3. **Model Selection**: Use quantized models (q4_K_M) for faster inference.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

## Links

- [AgentOps GitHub](https://github.com/AgentOps-AI/agentops)
- [AgentOps Docs](https://docs.agentops.ai)
- [DuckDB](https://duckdb.org)
- [Ollama](https://ollama.ai)
- [ClickHouse](https://clickhouse.com)
- [OpenTelemetry](https://opentelemetry.io)

