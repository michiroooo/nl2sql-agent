# NL2SQL Agent with AG2 Multi-Agent System# NL2SQL Agent with AgentOps Self-Hosting



Natural Language to SQL conversion system with autonomous multi-agent collaboration powered by AG2 (AutoGen).Natural Language to SQL conversion system with full AgentOps observability platform (self-hosted).



## Features## Features



- 🤖 **Multi-Agent Collaboration**: Three specialized AI agents working together- 🗣️ **Natural Language Interface**: Query databases using Japanese or English

  - **SQL Specialist**: Database schema analysis and SQL query generation- 🚀 **High Performance**: DuckDB for sub-100ms query execution

  - **Web Researcher**: Real-time web search and information gathering- � **AgentOps Self-Hosted**: Full observability stack with traces, metrics, and analytics

  - **Data Analyst**: Statistical analysis and predictions with code execution- 💬 **Chat Interface**: Streamlit for intuitive user experience

- 🗣️ **Natural Language Interface**: Query databases using Japanese natural language- 🇯🇵 **Japanese Support**: Optimized for Japanese e-commerce data

- 🚀 **High Performance**: DuckDB for sub-100ms query execution- � **Distributed Tracing**: OpenTelemetry integration for end-to-end visibility

- 📊 **Full Observability**: OpenTelemetry + ClickHouse for distributed tracing

- 💬 **Interactive UI**: Streamlit for intuitive multi-agent conversation## Architecture

- 🇯🇵 **Japanese Optimized**: LLM fine-tuned for Japanese e-commerce queries

```

## Architecture┌─────────────────────────────────────────────────────────────┐

│                        User Browser                          │

```└──────────┬────────────────────────────────┬─────────────────┘

┌─────────────────────────────────────────────────────────────┐           │                                │

│                        User Browser                          │           │ Port 8501                      │ Port 3000

└──────────────────────────┬───────────────────────────────────┘           ▼                                ▼

                           │ Port 8501┌─────────────────────┐          ┌─────────────────────┐

                           ▼│   Streamlit UI      │          │ AgentOps Dashboard  │

                ┌─────────────────────┐│  (Chat Interface)   │          │   (Next.js)         │

                │   Streamlit UI      │└──────────┬──────────┘          └──────────┬──────────┘

                │  (Chat Interface)   │           │                                │

                └──────────┬──────────┘           │ @agent, @operation             │ API Calls

                           │           ▼                                ▼

                           ▼┌─────────────────────┐          ┌─────────────────────┐

                ┌─────────────────────────────────┐│   NL2SQL Agent      │◄─────────┤  AgentOps API       │

                │  MultiAgentOrchestrator        ││  (with decorators)  │ Track    │   (FastAPI)         │

                │  (AG2 GroupChat Manager)       │└──────────┬──────────┘          └──────────┬──────────┘

                └──────────┬──────────────────────┘           │                                │

                           │           │ SQL Queries                    │ Store metadata

        ┌──────────────────┼──────────────────┐           ▼                                ▼

        │                  │                  │┌─────────────────────┐          ┌─────────────────────┐

        ▼                  ▼                  ▼│     DuckDB          │          │   PostgreSQL        │

┌──────────────┐  ┌──────────────┐  ┌──────────────┐│  (E-commerce Data)  │          │  (User/API Data)    │

│ SQL Agent    │  │ Web Agent    │  │ Reasoning    │└─────────────────────┘          └─────────────────────┘

│              │  │              │  │ Agent        │           │

│ • Schema     │  │ • DuckDuckGo │  │ • Python     │           │ Traces via OTLP

│   Analysis   │  │   Search     │  │   Execution  │           ▼

│ • SQL Gen    │  │ • Web Scrape │  │ • Statistics │┌─────────────────────┐

└──────┬───────┘  └──────┬───────┘  └──────┬───────┘│  OTel Collector     │

       │                 │                 ││  (Port 4318)        │

       │ MCP Tools       │ MCP Tools       │ MCP Tools└──────────┬──────────┘

       ▼                 ▼                 ▼           │

┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │ Store traces

│ DB Tools     │  │ Web Tools    │  │ Interpreter  │           ▼

└──────┬───────┘  └──────────────┘  └──────────────┘┌─────────────────────┐

       ││    ClickHouse       │

       │ SQL Queries│  (Traces & Metrics) │

       ▼└─────────────────────┘

┌─────────────────────┐```

│     DuckDB          │

│  (E-commerce Data)  │## Quick Start

└─────────────────────┘

       │### Prerequisites

       │ Traces via OTLP (Port 4318)

       ▼- Docker and Docker Compose

┌─────────────────────┐- At least 4GB RAM available

│  OTel Collector     │

└──────────┬──────────┘### 1. Clone Repository

           │

           ▼```bash

┌─────────────────────┐git clone https://github.com/michiroooo/nl2sql-agent.git

│    ClickHouse       │cd nl2sql-agent

│  (Traces & Metrics) │```

└─────────────────────┘

```### 2. Setup Environment



## System Components```bash

cp .env.example .env

### 1. MultiAgentOrchestrator (`ag2_orchestrator.py`)# Edit .env and set a secure JWT_SECRET_KEY

```

**Role**: Coordinates multi-agent collaboration using AG2's GroupChat pattern.

**Required environment variables:**

**Key Classes**:- `JWT_SECRET_KEY`: Set a random 32+ character string for JWT signing

- `AgentConfig`: LLM configuration for Ollama endpoint- `CLICKHOUSE_PASSWORD`: Password for ClickHouse (default: `password`)

- `MultiAgentOrchestrator`: Main orchestration class managing agent interactions- `POSTGRES_PASSWORD`: Password for PostgreSQL (default: `postgres`)



**Communication Flow**:### 3. Generate Sample Database

1. User query received from Streamlit

2. Orchestrator creates GroupChat with all agents```bash

3. GroupChatManager automatically selects appropriate agentcd data

4. Agents collaborate through message passingpip install -r requirements.txt

5. Final result returned to userpython setup_database.py

cd ..

**Key Methods**:```

```python

execute(query: str) -> dict[str, Any]### 4. Start All Services

```

- Executes query using multi-agent collaboration```bash

- Returns conversation history and participating agentsdocker compose up -d

```

### 2. Specialized Agents

This will start:

#### SQL Agent (`create_sql_agent()`)- **Streamlit UI** (Port 8501) - Chat interface

- **Purpose**: Database specialist for schema analysis and SQL generation- **AgentOps Dashboard** (Port 3000) - Observability dashboard

- **Tools**: `get_database_schema()`, `execute_sql_query()`- **AgentOps API** (Port 8000) - Backend API

- **Behavior**: Analyzes user intent, generates SQL, executes queries- **Ollama** (Port 11434) - LLM inference

- **ClickHouse** (Port 8123, 9000) - Trace storage

#### Web Agent (`create_web_agent()`)- **PostgreSQL** (Port 5432) - Metadata storage

- **Purpose**: Web research specialist for external information- **OTel Collector** (Port 4317, 4318) - Trace collection

- **Tools**: `web_search()`, `scrape_webpage()`

- **Behavior**: Searches web, scrapes content, summarizes findings### 5. Download Ollama Model



#### Reasoning Agent (`create_reasoning_agent()`)```bash

- **Purpose**: Data analyst with code execution capabilitiesdocker exec -it nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M

- **Tools**: `python_interpreter()`, LocalCommandLineCodeExecutor```

- **Behavior**: Statistical analysis, predictions, data visualization

### 6. Access Interfaces

### 3. MCP Tools (`mcp_tools/`)

- **Streamlit UI**: http://localhost:8501

**Model Context Protocol (MCP)** provides standardized tool interfaces for agents.- **AgentOps Dashboard**: http://localhost:3000

- **AgentOps API Docs**: http://localhost:8000/docs

#### Database Tools (`database.py`)

```python## Usage

create_database_tools() -> dict[str, Callable]

```### Example Queries

- `get_database_schema(query)`: Returns table schemas with row counts

- `execute_sql_query(sql)`: Executes SQL with 50-row limit**Japanese:**

```

#### Web Tools (`web.py`)顧客数を教えて

```python2024年で最も売れた商品の名前と売上個数を教えて

create_web_tools() -> dict[str, Callable]東京都在住の顧客数を教えて

```購入金額トップ3の顧客名と購入金額を教えて

- `web_search(query)`: DuckDuckGo API search (top 5 results)```

- `scrape_webpage(url)`: HTML content extraction (2000 char limit)

**English:**

#### Interpreter Tool (`interpreter.py`)```

```pythonShow me the number of customers

create_interpreter_tool() -> dict[str, Callable]What product sold the most in 2024?

```How many customers are from Tokyo?

- `python_interpreter(code)`: Safe Python execution with whitelistShow top 3 customers by purchase amount

  - Allowed: math, statistics, datetime, json, re```

  - Blocked: File I/O, network, system calls

See `data/sample_queries.md` for more examples.

### 4. Streamlit UI (`ui/app.py`)

### Viewing Traces in AgentOps Dashboard

**Role**: Interactive chat interface with agent conversation visualization.

1. Open http://localhost:3000

**Features**:2. Navigate to **Traces** section

- Query input with sample buttons3. View detailed execution traces with:

- Agent conversation history display   - Operation timeline

- Real-time agent message streaming   - SQL query generation steps

- Participating agents summary   - Database execution times

   - LLM prompts and responses

**Key Components**:   - Error traces

```python

MultiAgentOrchestrator(## Development

    model="qwen2.5-coder:7b-instruct-q4_K_M",

    base_url="http://ollama:11434"### Project Structure

)

``````

.

## Module Communication├── docker-compose.yml

├── agentops/

### 1. User → UI → Orchestrator│   ├── otel-collector-config.yaml  # OTel configuration

```│   └── clickhouse/

User Input (Streamlit)│       └── migrations/

    → st.text_area(query)│           └── 0000_init.sql       # ClickHouse schema

    → orchestrator.execute(query)├── ui/

    → GroupChat initialization│   ├── app.py            # Streamlit UI

```│   ├── Dockerfile

│   └── requirements.txt

### 2. Orchestrator → Agents├── function/

```│   ├── agent.py          # NL2SQL agent (with @agent, @operation)

GroupChatManager│   ├── database.py       # DuckDB manager

    → speaker_selection_method="auto"│   └── requirements.txt

    → Select appropriate agent based on context├── data/

    → Agent.receive(message)│   ├── setup_database.py # Sample data generator

```│   └── ecommerce.db      # DuckDB database

└── docs/

### 3. Agent → MCP Tools    └── design.md         # Design document

``````

Agent.register_function(tool)

    → Tool invocation via function_map### Local Development

    → Tool execution in safe sandbox

    → Result returned to agent```bash

```# Install dependencies

cd function

### 4. Agent → Databasepip install -r requirements.txt

```

SQL Agent# Start FastAPI server

    → execute_sql_query(sql)uvicorn main:app --reload --port 8001

    → DuckDB connection (DATABASE_PATH)```

    → Query execution + formatting

    → Result (max 50 rows)### Database Schema

```

```sql

### 5. Telemetry → ClickHouse-- Customers

```customer_id, customer_name, prefecture, registration_date

All Operations

    → OpenTelemetry instrumentation-- Products

    → OTLP export (HTTP 4318)product_id, product_name, category, price, stock_quantity

    → OTel Collector processing

    → ClickHouse storage (otel_2.otel_traces)-- Orders

```order_id, customer_name, product_id, quantity, order_date, total_amount

```

## Quick Start

## Configuration

### Prerequisites

### Environment Variables

- Docker and Docker Compose

- At least 8GB RAM (for Ollama + agents)| Variable | Description | Default |

- 10GB disk space (for models)|----------|-------------|---------|

| `AGENTOPS_API_KEY` | AgentOps API key (optional for self-hosted) | - |

### 1. Clone Repository| `AGENTOPS_API_ENDPOINT` | AgentOps API endpoint | `http://localhost:8000` |

| `AGENTOPS_EXPORTER_ENDPOINT` | OTLP exporter endpoint | `http://localhost:4318/v1/traces` |

```bash| `DATABASE_PATH` | Path to DuckDB file | `/app/data/ecommerce.db` |

git clone https://github.com/michiroooo/nl2sql-agent.git| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://ollama:11434` |

cd nl2sql-agent| `OLLAMA_MODEL` | LLM model name | `qwen2.5-coder:7b-instruct-q4_K_M` |

```| `JWT_SECRET_KEY` | JWT signing secret (32+ chars) | **Required** |

| `CLICKHOUSE_PASSWORD` | ClickHouse password | `password` |

### 2. Setup Environment| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |



```bash### AgentOps Decorators

cp .env.example .env

# Edit .env if needed (default values work)The agent uses AgentOps decorators for automatic tracing:

```

```python

**Key environment variables**:from agentops.sdk.decorators import agent, operation

- `DATABASE_PATH=/app/data/ecommerce.db` - DuckDB location

- `OLLAMA_MODEL=qwen2.5-coder:7b-instruct-q4_K_M` - LLM model@agent

- `OLLAMA_BASE_URL=http://ollama:11434` - Ollama endpointclass NL2SQLAgent:

    @operation

### 3. Generate Sample Database    def _generate_sql(self, question: str) -> str:

        # Automatically tracked

```bash        pass

cd data    

pip install -r requirements.txt    @operation

python setup_database.py    def process_query(self, user_input: str) -> dict:

cd ..        # Automatically tracked

```        pass

```

This creates:

- **customers** table: 200 Japanese e-commerce customers## Monitoring & Observability

- **orders** table: 500 orders with products

- **products** table: 20 Japanese products### Metrics Available



### 4. Start AG2 Multi-Agent System- **Query Performance**: End-to-end latency, SQL generation time, DB execution time

- **Success Rates**: Query success/failure rates, error types

```bash- **LLM Usage**: Token counts, model performance, prompt effectiveness

docker compose -f docker-compose-ag2.yml up -d- **System Health**: Database connection status, service availability

```

### Trace Details

This starts:

- **ClickHouse** (Ports 8123, 9000) - Trace storageEach query generates a trace with:

- **OTel Collector** (Ports 4317, 4318, 8888) - Telemetry pipeline1. **Agent Span**: Overall query processing

- **Ollama** (Port 11434) - LLM inference2. **SQL Generation Operation**: LLM prompt and generated SQL

- **Streamlit UI** (Port 8501) - Multi-agent interface3. **Database Execution**: Query execution time and results

4. **Formatting**: Result formatting duration

### 5. Download LLM Model

## Troubleshooting

```bash

docker exec nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M### Services Not Starting

```

```bash

This downloads ~4.7GB model optimized for:# Check all container status

- Japanese language understandingdocker compose ps

- Code generation (SQL, Python)

- Instruction following# View logs for specific service

docker compose logs -f streamlit-ui

### 6. Access Systemdocker compose logs -f agentops-api

docker compose logs -f clickhouse

- **Streamlit UI**: http://localhost:8501```

- **ClickHouse**: http://localhost:8123 (user: default, password: password)

- **OTel Collector Health**: http://localhost:8888/metrics### ClickHouse Connection Error



## Usage Examples```bash

# Verify ClickHouse is healthy

### Example 1: Database Querydocker exec -it nl2sql-clickhouse clickhouse-client --query "SELECT 1"

```

User: "2024年で最も売れた商品は？"# Check schema creation

docker exec -it nl2sql-clickhouse clickhouse-client --query "SHOW DATABASES"

Agent Flow:```

1. SQL Agent: Analyzes schema → Generates SQL

2. SQL Agent: Executes query → Returns top product### AgentOps Dashboard Not Loading

3. Result: "商品名: ワイヤレスイヤホン, 売上個数: 45個"

``````bash

# Check API connectivity

### Example 2: Web Research + Analysiscurl http://localhost:8000/health

```

User: "最新のEコマーストレンドを調査して、当社の売上データと比較して"# Check dashboard logs

docker compose logs -f agentops-dashboard

Agent Flow:```

1. Web Agent: DuckDuckGo search → Scrapes articles

2. SQL Agent: Fetches sales data from database### Ollama Connection Error

3. Reasoning Agent: Statistical comparison → Insights

4. Result: Multi-agent collaborative analysis```bash

```# Check Ollama is running

docker logs nl2sql-ollama

### Example 3: Predictive Analysis

```# Verify model is downloaded

User: "明日の売上を予測して"docker exec -it nl2sql-ollama ollama list

```

Agent Flow:

1. SQL Agent: Historical sales data retrieval### Database Not Found

2. Reasoning Agent: Python time-series analysis

3. Reasoning Agent: Prediction with confidence interval```bash

4. Result: "予測売上: ¥1,234,567 ± ¥50,000"# Regenerate database

```cd data

python setup_database.py

## Sample Queries```



### Database Queries (SQL Agent)## Performance Tips

- "顧客数を教えて"

- "2024年で最も売れた商品の名前と売上個数を教えて"1. **ClickHouse**: Traces are kept for 3 days (TTL). Adjust in migration SQL if needed.

- "東京都の顧客の平均購入金額は？"2. **Memory**: Allocate at least 4GB RAM for all services.

3. **Model Selection**: Use quantized models (q4_K_M) for faster inference.

### Web Research (Web Agent)

- "最新のEコマーストレンドを調査して"## Contributing

- "DuckDBの公式ドキュメントから使い方を教えて"

1. Fork the repository

### Data Analysis (Multi-Agent)2. Create a feature branch (`git checkout -b feature/amazing-feature`)

- "今日の売上データから明日の売上を予測して"3. Commit your changes (`git commit -m 'Add amazing feature'`)

- "顧客セグメント分析を実施して改善提案をして"4. Push to the branch (`git push origin feature/amazing-feature`)

5. Open a Pull Request

## Configuration

## License

### Ollama Models

MIT License

Default: `qwen2.5-coder:7b-instruct-q4_K_M` (4.7GB)

## Links

Alternative models:

```bash- [AgentOps GitHub](https://github.com/AgentOps-AI/agentops)

# Smaller model (1.7GB, faster but less capable)- [AgentOps Docs](https://docs.agentops.ai)

docker exec nl2sql-ollama ollama pull gemma2:2b-instruct-q4_K_M- [DuckDB](https://duckdb.org)

- [Ollama](https://ollama.ai)

# Update docker-compose-ag2.yml:- [ClickHouse](https://clickhouse.com)

environment:- [OpenTelemetry](https://opentelemetry.io)

  OLLAMA_MODEL: gemma2:2b-instruct-q4_K_M

```

### Agent Behavior

Edit `function/ag2_orchestrator.py`:

**Max conversation rounds**:
```python
self.group_chat = GroupChat(
    agents=[...],
    max_round=10  # Increase for complex queries
)
```

**Temperature (creativity)**:
```python
AgentConfig(temperature=0.0)  # 0.0=deterministic, 1.0=creative
```

### Tool Security

Edit `function/mcp_tools/interpreter.py`:

**Allowed imports**:
```python
ALLOWED_IMPORTS = {'math', 'statistics', 'datetime', 'json', 're'}
```

## Observability

### ClickHouse Queries

**View traces**:
```sql
SELECT 
    Timestamp, 
    ServiceName, 
    SpanName, 
    Duration
FROM otel_2.otel_traces
ORDER BY Timestamp DESC
LIMIT 100;
```

**Agent performance**:
```sql
SELECT 
    SpanAttributes['agent.name'] as agent,
    AVG(Duration) as avg_duration_ns,
    COUNT(*) as invocations
FROM otel_2.otel_traces
WHERE SpanName LIKE '%agent%'
GROUP BY agent;
```

### OTel Collector Metrics

```bash
curl http://localhost:8888/metrics
```

## Development

### Project Structure

```
nl2sql-agent/
├── function/
│   ├── ag2_orchestrator.py      # Multi-agent orchestration
│   ├── database.py               # DuckDB connection
│   ├── main.py                   # FastAPI entry (legacy)
│   ├── mcp_tools/
│   │   ├── database.py           # DB tools
│   │   ├── web.py                # Web tools
│   │   └── interpreter.py        # Code execution
│   ├── requirements.txt
│   └── Dockerfile
├── ui/
│   ├── app.py                    # Streamlit interface
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── setup_database.py         # Sample data generation
│   └── sample_queries.md
├── agentops/
│   ├── otel-collector-config.yaml
│   └── clickhouse/
│       └── migrations/
│           └── 0000_init.sql
├── docker-compose-ag2.yml        # AG2 deployment
└── README.md
```

### Adding New Tools

1. Create tool in `function/mcp_tools/`:
```python
def create_new_tool() -> dict[str, Callable]:
    def tool_function(param: str) -> str:
        # Implementation
        return result
    
    return {"tool_name": tool_function}
```

2. Register in agent:
```python
tools = create_new_tool()
agent.register_function(function_map=tools)
```

### Adding New Agent

1. Define in `ag2_orchestrator.py`:
```python
def create_new_agent(config: AgentConfig) -> AssistantAgent:
    return AssistantAgent(
        name="specialist_name",
        system_message="Role description...",
        llm_config=config.llm_config
    )
```

2. Add to orchestrator:
```python
self.new_agent = create_new_agent(config)
self.group_chat = GroupChat(
    agents=[..., self.new_agent],
    ...
)
```

## Troubleshooting

### Issue: Agents not responding

**Check Ollama**:
```bash
docker logs nl2sql-ollama --tail 50
docker exec nl2sql-ollama ollama list
```

**Solution**: Ensure model is downloaded
```bash
docker exec nl2sql-ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M
```

### Issue: Import errors

**Check pyautogen version**:
```bash
docker exec nl2sql-streamlit pip show pyautogen
```

**Expected**: `Version: 0.2.35` (not 0.10.0)

**Solution**: Rebuild with correct version
```bash
docker compose -f docker-compose-ag2.yml build --no-cache streamlit-ui
```

### Issue: Database connection failed

**Check DuckDB**:
```bash
docker exec nl2sql-streamlit ls -la /app/data/
```

**Solution**: Generate database
```bash
cd data
python setup_database.py
```

### Issue: Traces not appearing in ClickHouse

**Check OTel Collector**:
```bash
docker logs nl2sql-otel-collector --tail 50
```

**Expected**: "Everything is ready. Begin running and processing data."

**Check ClickHouse**:
```bash
docker exec nl2sql-clickhouse clickhouse-client --password password --query "SELECT COUNT(*) FROM otel_2.otel_traces"
```

## Performance

### Benchmarks (Apple M4 Max, 128GB RAM)

| Query Type | Agent Selection | Execution Time | Token Usage |
|------------|----------------|----------------|-------------|
| Simple SQL | SQL Agent | 2-5s | ~500 tokens |
| Web Search | Web Agent | 5-10s | ~800 tokens |
| Analysis | Multi-Agent | 15-30s | ~2000 tokens |

### Optimization Tips

1. **Reduce max_round**: Lower for simple queries
2. **Use smaller model**: gemma2:2b for faster responses
3. **Limit tool results**: Reduce row limits in tools
4. **Enable caching**: LLM response caching in Ollama

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## References

- [AG2 (AutoGen) Documentation](https://microsoft.github.io/autogen/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Ollama Models](https://ollama.com/library)

## Support

For issues and questions:
- GitHub Issues: https://github.com/michiroooo/nl2sql-agent/issues
- Documentation: See `/docs` directory
