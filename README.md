# NL2SQL Agent with Open WebUI

Natural Language to SQL conversion system using Open WebUI frontend with AgentOps monitoring.

## Features

- 🗣️ **Natural Language Interface**: Query databases using Japanese or English
- 🚀 **High Performance**: DuckDB for sub-100ms query execution
- 🔍 **AgentOps Monitoring**: Track agent behavior and performance
- 💬 **Chat Interface**: Open WebUI for intuitive user experience
- 🇯🇵 **Japanese Support**: Optimized for Japanese e-commerce data

## Architecture

```
Open WebUI (Port 3000) → FastAPI Backend (Port 8001) → DuckDB + Ollama + AgentOps
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) NVIDIA GPU for faster inference

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
docker-compose up -d
```

### 5. Download Ollama Model

```bash
docker exec -it nl2sql-ollama ollama pull gemma2:9b-instruct-fp16
```

### 6. Access Open WebUI

Open http://localhost:3000 in your browser.

## Usage

### Example Queries

**Japanese:**
```
在庫が10個以下の商品を教えて
2024年10月の商品カテゴリ別売上合計を教えて
東京都在住の顧客で購入金額が10万円以上の人を抽出して
```

**English:**
```
Show me products with stock less than 10
Calculate total sales by category for October 2024
List Tokyo customers who spent over 100,000 yen
```

See `data/sample_queries.md` for more examples.

## API Endpoints

### Health Check
```bash
curl http://localhost:8001/health
```

### Get Database Schema
```bash
curl http://localhost:8001/schema
```

### Query via API
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "在庫が10個以下の商品を教えて"}'
```

## Development

### Project Structure

```
.
├── docker-compose.yml
├── function/
│   ├── main.py           # FastAPI app
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
