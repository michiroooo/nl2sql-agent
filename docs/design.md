# NL2SQL Agent System Design Document

## 1. Overview

Natural language to SQL conversion system using Open WebUI as frontend with custom function backend for AgentOps integration.

### Architecture Goals

- Leverage Open WebUI for chat interface and user management
- Implement custom NL2SQL function with AgentOps monitoring
- Use DuckDB for high-performance SQL queries
- Support Japanese natural language queries

## 2. Technology Stack

### Core Components

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Frontend | Open WebUI | latest | Chat interface |
| LLM | Ollama (gemma2:9b-instruct-fp16) | latest | Japanese language support |
| Database | DuckDB | 0.9+ | High-speed SQL engine |
| Backend | FastAPI | 0.104+ | Custom function API |
| Monitoring | AgentOps | 0.2+ | Agent observability |
| Container | Docker Compose | 3.8+ | Service orchestration |

### Why gemma2:9b-instruct-fp16?

- **Superior Japanese language understanding** compared to Llama
- Instruction-tuned for structured outputs (SQL generation)
- Balanced performance on consumer hardware

## 3. System Architecture

```
┌─────────────────┐
│   Open WebUI    │ ← User Interface (Port 3000)
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│ Custom Function │ ← NL2SQL Logic (Port 8001)
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    ↓         ↓          ↓
┌────────┐ ┌──────┐ ┌─────────┐
│ Ollama │ │DuckDB│ │AgentOps │
└────────┘ └──────┘ └─────────┘
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

## 5. Implementation Plan

### Phase 1: Infrastructure Setup (Day 1)

- [x] Docker Compose configuration for all services
- [x] Open WebUI deployment with Ollama integration
- [x] DuckDB initialization with sample data
- [x] Network configuration between containers

### Phase 2: Backend Development (Day 2-3)

- [x] FastAPI custom function structure
- [x] LangChain SQL agent implementation
- [x] AgentOps integration for monitoring
- [x] Error handling and validation logic

### Phase 3: Integration & Testing (Day 4)

- [ ] Open WebUI function registration
- [ ] End-to-end query testing
- [ ] Performance optimization
- [ ] Japanese language query validation

### Phase 4: Documentation & Deployment (Day 5)

- [x] API documentation
- [x] User guide for query patterns
- [x] Deployment instructions
- [ ] AgentOps dashboard setup

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
