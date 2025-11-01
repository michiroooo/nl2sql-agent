# NL2SQL Agent with Streamlit

Natural Language to SQL conversion system using Streamlit UI with AgentOps monitoring.

## Features

- 🗣️ **Natural Language Interface**: Query databases using Japanese or English
- 🚀 **High Performance**: DuckDB for sub-100ms query execution
- 🔍 **AgentOps Monitoring**: Track agent behavior and performance
- 💬 **Chat Interface**: Streamlit for intuitive user experience
- 🇯🇵 **Japanese Support**: Optimized for Japanese e-commerce data
- 📊 **Data Visualization**: View SQL queries and results inline

## Architecture

```
Streamlit UI (Port 8501) → NL2SQL Agent → DuckDB + Ollama + AgentOps
```

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
docker exec -it nl2sql-ollama ollama pull gemma2:2b-instruct-q4_K_M
```

### 6. Access Streamlit UI

Open http://localhost:8501 in your browser.

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

## Development

### Project Structure

```
.
├── docker-compose.yml
├── ui/
│   ├── app.py            # Streamlit UI
│   ├── Dockerfile
│   └── requirements.txt
├── function/
│   ├── agent.py          # NL2SQL agent
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
| `AGENTOPS_API_KEY` | AgentOps API key | (optional) |
| `DATABASE_PATH` | Path to DuckDB file | `/app/data/ecommerce.db` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://ollama:11434` |
| `OLLAMA_MODEL` | LLM model name | `gemma2:9b-instruct-fp16` |

## Monitoring

If AgentOps API key is configured, visit https://app.agentops.ai to view:
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

- [Open WebUI](https://github.com/open-webui/open-webui)
- [AgentOps](https://agentops.ai)
- [DuckDB](https://duckdb.org)
- [Ollama](https://ollama.ai)
