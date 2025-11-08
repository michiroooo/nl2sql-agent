# AG2 Multi-Agent System Architecture with MCP Integration

本ドキュメントでは、AG2 (AutoGen) フレームワークとModel Context Protocol (MCP) を使用したマルチエージェントシステムのアーキテクチャ、モジュール間通信、各クラスの役割について詳細に解説します。

## 目次

1. [システム概要](#システム概要)
2. [MCP統合](#mcp統合)
3. [アーキテクチャ図](#アーキテクチャ図)
4. [コンポーネント詳細](#コンポーネント詳細)
5. [モジュール間通信フロー](#モジュール間通信フロー)
6. [クラス設計](#クラス設計)
7. [データフロー](#データフロー)
8. [エラーハンドリング](#エラーハンドリング)

---

## システム概要

### 設計思想

AG2マルチエージェントシステムは、**専門化と協調**の原則に基づいて設計され、**Model Context Protocol (MCP)** により標準化されたツール通信を実現しています。

**コアコンセプト**:

- **専門エージェント**: SQL、Web検索、推論の3つの専門領域に特化
- **自律的協調**: GroupChatパターンによる自動的なエージェント選択
- **MCP標準化**: HTTP JSON-RPC による統一ツールインターフェース
- **マイクロサービス**: MCPサーバーの独立デプロイと拡張性
- **完全な可観測性**: Phoenix (Arize AI) による自動LLMトレーシング + MCPログ

### 技術スタック

| レイヤー | 技術 | 役割 |
|---------|------|------|
| UI | Streamlit | マルチエージェント対話インターフェース |
| オーケストレーション | AG2 (pyautogen 0.2.35) | エージェント協調管理 |
| LLM | Ollama (qwen2.5-coder:7b) | 自然言語理解・生成 |
| ツールプロトコル | MCP (HTTP JSON-RPC) | 標準化ツールインターフェース |
| MCPサーバー | FastAPI + Uvicorn | ツール実行エンドポイント |
| データベース | DuckDB | 高速SQL実行 |
| 可観測性 | Phoenix (Arize AI) | 自動LLMトレーシング |
| デプロイ | Docker Compose | 4サービスオーケストレーション |

---

## MCP統合

### Model Context Protocolとは

**MCP (Model Context Protocol)** は、AIエージェントと外部ツール間の標準化された通信プロトコルです。

**主な特徴**:

- JSON-RPC 2.0ベースの統一インターフェース
- ツール定義とスキーマの標準化
- クライアント/サーバー分離による拡張性
- 言語・フレームワーク非依存

### 本システムでの実装

```text
┌─────────────────┐
│  AG2 Agents     │
└────────┬────────┘
         │ Function Call
         ▼
┌─────────────────┐
│  MCP Tools      │  httpx.post()
│  (HTTP Client)  │─────────────────┐
└─────────────────┘                 │
                                    │ HTTP
                                    ▼
                         ┌──────────────────────┐
                         │  MCP Server          │
                         │  (FastAPI)           │
                         │  Port 8080           │
                         └──────────┬───────────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │ DuckDB   │
                              └──────────┘
```

**リクエスト例**:

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

**レスポンス例**:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"customer_count\": 200}]"
      }
    ]
  }
}
```

---

## アーキテクチャ図

### 全体アーキテクチャ

```text
┌────────────────────────────────────────────────────────────────┐
│                        User Browser                             │
│                    (http://localhost:8501)                      │
└─────────────────────────────┬──────────────────────────────────┘
                              │ HTTP Request
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Streamlit UI (ui/app.py)                   │
│                                                                  │
│  • Session state management                                     │
│  • Query input interface                                        │
│  • Conversation history display                                 │
│  • Agent activity visualization                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │ orchestrator.execute(query)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│          MultiAgentOrchestrator (function/ag2_orchestrator.py)  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              GroupChatManager                            │   │
│  │  • speaker_selection_method="auto"                      │   │
│  │  • max_round=10                                         │   │
│  │  • Conversation coordination                            │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│      ┌──────────────┼──────────────┐                            │
│      │              │              │                            │
│      ▼              ▼              ▼                            │
│  ┌────────┐    ┌────────┐    ┌──────────┐                      │
│  │SQL     │    │Web     │    │Reasoning │                      │
│  │Agent   │    │Agent   │    │Agent     │                      │
│  └───┬────┘    └───┬────┘    └────┬─────┘                      │
│      │             │              │                             │
└──────┼─────────────┼──────────────┼─────────────────────────────┘
       │             │              │
       │ register_function()        │
       ▼             ▼              ▼
┌──────────────────────────────────────────┐
│     MCP Tools (mcp_tools/*.py)           │
│                                          │
│  • database.py: HTTP client for MCP     │
│  • web.py: DuckDuckGo search            │
│  • interpreter.py: Safe Python exec     │
└─────────────┬────────────────────────────┘
              │
              │ HTTP POST (JSON-RPC)
              ▼
┌─────────────────────────────────────────┐
│   MCP Server (mcp_server/server.py)    │
│   FastAPI + Uvicorn                    │
│   http://mcp-server:8080               │
│                                         │
│  Endpoints:                             │
│  • POST /mcp        Tool execution     │
│  • GET  /health     Health check       │
└─────────────┬───────────────────────────┘
              │
              │ SQL Query
              ▼
┌─────────────────────┐
│      DuckDB         │
│  (ecommerce.db)     │
│                     │
│  • customers (200)  │
│  • orders (500)     │
│  • products (20)    │
└─────────────────────┘

[All components]
     │ Auto-instrumentation + HTTP logs
     ▼
┌─────────────────────┐
│   Phoenix Server    │
│  (http://localhost  │
│       :6006)        │
│                     │
│  • Trace collector  │
│  • UI dashboard     │
│  • MCP spans        │
└─────────────────────┘
```

---

## コンポーネント詳細

### 1. Streamlit UI (`ui/app.py`)

**責務**: ユーザーインターフェースとセッション管理

**主要機能**:

```python
@st.cache_resource
def get_orchestrator() -> MultiAgentOrchestrator:
    """オーケストレータのシングルトンインスタンスを取得"""
    return MultiAgentOrchestrator(work_dir=Path("/tmp/ag2_workspace"))
```

**ステート管理**:

- `st.session_state.messages`: 会話履歴
- オーケストレータキャッシュによるパフォーマンス最適化

**UIコンポーネント**:

1. **クエリ入力**: `st.chat_input()` でユーザー入力
2. **サンプルボタン**: よくあるクエリのクイックアクセス
3. **会話表示**: `st.chat_message()` でメッセージ表示
4. **エージェント活動**: expander内でエージェント会話を可視化

---

### 2. MCP Server (`mcp_server/server.py`)

**責務**: 標準化されたツール実行エンドポイント

**主要機能**:

```python
@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """JSON-RPC 2.0リクエストを処理"""
    if request.method != "tools/call":
        raise ValueError(f"Unsupported method: {request.method}")

    tool_name = request.params.name
    arguments = request.params.arguments

    if tool_name == "query":
        return await execute_query(request.id, arguments)

    raise ValueError(f"Unknown tool: {tool_name}")

async def execute_query(request_id: int, arguments: dict[str, Any]) -> MCPResponse:
    """SQLクエリを実行して結果を返す"""
    query = arguments.get("query", "")
    conn = duckdb.connect(DB_PATH, read_only=READ_ONLY)
    result = conn.execute(query).fetchall()

    return MCPResponse(
        jsonrpc="2.0",
        id=request_id,
        result={"content": [{"type": "text", "text": str(result)}]}
    )
```

**エンドポイント**:

- `POST /mcp`: JSON-RPC 2.0ツール実行
- `GET /health`: ヘルスチェック

**環境変数**:

- `MCP_DB_PATH`: DuckDBデータベースパス
- `MCP_READ_ONLY`: 読み取り専用モード (デフォルト: true)

---

### 3. MCP Tools (`mcp_tools/database.py`)

**責務**: AG2エージェントからMCPサーバーへのHTTPクライアント

**主要機能**:

```python
def _call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    """MCPサーバーにHTTP POSTでツール実行リクエストを送信"""
    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8080/mcp")

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments}
    }

    try:
        response = httpx.post(mcp_url, json=request, timeout=30.0)
        response.raise_for_status()
        result = response.json()

        if "error" in result and result["error"]:
            raise RuntimeError(f"MCP error: {result['error']}")

        return result.get("result", {})

    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        # Fallback to direct DuckDB access
        return _fallback_direct_query(arguments)

def get_database_schema() -> str:
    """データベーススキーマを取得 (MCPサーバー経由)"""
    result = _call_mcp_tool("query", {
        "query": "SELECT table_name, column_name, data_type FROM information_schema.columns"
    })
    return _format_schema_from_rows(result)

def execute_sql_query(query: str) -> str:
    """SQLクエリを実行 (MCPサーバー経由)"""
    result = _call_mcp_tool("query", {"query": query})
    return _format_query_results(result)
```

**特徴**:

- HTTP JSON-RPC による標準化通信
- フォールバック機能 (MCP障害時に直接DuckDB接続)
- 結果のフォーマット処理
- エラーハンドリングと再試行

---

### 4. MultiAgentOrchestrator (`function/ag2_orchestrator.py`)

**責務**: マルチエージェント協調のオーケストレーション

#### AgentConfig

```python
class AgentConfig:
    """エージェント設定の統一管理"""

    def __init__(self, model: str | None = None,
                 base_url: str | None = None,
                 temperature: float = 0.0):
        self.llm_config = {
            "config_list": [{
                "model": model,
                "base_url": base_url,
                "api_key": "ollama",
            }],
            "temperature": temperature,
        }
```

**設計意図**:

- 環境変数からのデフォルト値取得
- 全エージェントで統一されたLLM設定
- `temperature=0.0` で決定論的な動作を保証

#### 専門エージェント

**SQL Agent**:

- データベースクエリの専門家
- MCP経由でスキーマ取得とSQL実行
- 結果を自然言語で要約

**Web Agent**:

- Web情報収集の専門家
- DuckDuckGo検索とWebスクレイピング
- 情報統合と要約

**Reasoning Agent**:

- データ分析・予測の専門家
- サンドボックス化されたPython実行
- 統計分析と可視化

---

## モジュール間通信フロー

### MCP統合による通信パターン

```text
User Query
    │
    ▼
Streamlit UI
    │ orchestrator.execute(query)
    ▼
GroupChatManager
    │ LLM-based agent selection
    ▼
SQL Agent (selected)
    │ register_function call
    ▼
MCP Tools (database.py)
    │ _call_mcp_tool("query", {...})
    ▼
HTTP POST /mcp
    │ JSON-RPC 2.0
    ▼
MCP Server (FastAPI)
    │ execute_query()
    ▼
DuckDB
    │ SQL execution
    ▼
MCP Server
    │ MCPResponse with results
    ▼
MCP Tools
    │ _format_query_results()
    ▼
SQL Agent
    │ Natural language summary
    ▼
GroupChatManager
    │ Conversation coordination
    ▼
Streamlit UI
    │ Display results
    ▼
User
```

### シーケンス図

#### 典型的なクエリフロー (MCP統合版)

```text
User    Streamlit    Orchestrator    GroupChat    SQLAgent    MCPTools    MCPServer    DuckDB
 │          │             │             │            │           │           │          │
 │──query──>│             │             │            │           │           │          │
 │          │──execute───>│             │            │           │           │          │
 │          │             │─initiate───>│            │           │           │          │
 │          │             │             │──select───>│           │           │          │
 │          │             │             │            │──schema──>│           │          │
 │          │             │             │            │           │─POST /mcp>│          │
 │          │             │             │            │           │           │─SELECT──>│
 │          │             │             │            │           │           │<─result──│
 │          │             │             │            │           │<─response─│          │
 │          │             │             │            │<─schema───│           │          │
 │          │             │             │            │──query───>│           │          │
 │          │             │             │            │           │─POST /mcp>│          │
 │          │             │             │            │           │           │─SQL────>│
 │          │             │             │            │           │           │<─rows───│
 │          │             │             │            │           │<─response─│          │
 │          │             │             │            │<─result───│           │          │
 │          │             │             │<─message───│           │           │          │
 │          │             │<─conv──────│             │           │           │          │
 │          │<─results────│             │             │           │           │          │
 │<─display─│             │             │             │           │           │          │
```

---

## クラス設計

### クラス図

```text
┌─────────────────────────────────────────────────────────┐
│                   MultiAgentOrchestrator                │
├─────────────────────────────────────────────────────────┤
│ - sql_agent: AssistantAgent                             │
│ - web_agent: AssistantAgent                             │
│ - reasoning_agent: AssistantAgent                       │
│ - user_proxy: UserProxyAgent                            │
│ - group_chat: GroupChat                                 │
│ - manager: GroupChatManager                             │
├─────────────────────────────────────────────────────────┤
│ + execute(query: str) -> dict[str, Any]                 │
│ + _extract_conversation() -> list[dict]                 │
└─────────────────────────────────────────────────────────┘
                      │
                      │ uses
                      ▼
┌─────────────────────────────────────────────────────────┐
│                      AgentConfig                        │
├─────────────────────────────────────────────────────────┤
│ + llm_config: dict                                      │
├─────────────────────────────────────────────────────────┤
│ + __init__(model, base_url, temperature)               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   MCPServer (FastAPI)                   │
├─────────────────────────────────────────────────────────┤
│ - DB_PATH: str                                          │
│ - READ_ONLY: bool                                       │
├─────────────────────────────────────────────────────────┤
│ + handle_mcp_request(request: MCPRequest)               │
│   -> MCPResponse                                        │
│ + execute_query(id: int, args: dict) -> MCPResponse     │
│ + health_check() -> dict                                │
└─────────────────────────────────────────────────────────┘
                      │
                      │ called by
                      ▼
┌─────────────────────────────────────────────────────────┐
│              MCP Tools (HTTP Client)                    │
├─────────────────────────────────────────────────────────┤
│ + _call_mcp_tool(name: str, args: dict) -> Any          │
│ + _fallback_direct_query(args: dict) -> Any             │
│ + get_database_schema() -> str                          │
│ + execute_sql_query(sql: str) -> str                    │
│ + _format_schema_from_rows(result: dict) -> str         │
│ + _format_query_results(result: dict) -> str            │
└─────────────────────────────────────────────────────────┘
```

### 責務分離の原則

| クラス | 責務 | 依存関係 |
|-------|------|---------|
| `MultiAgentOrchestrator` | エージェント協調管理 | AG2 framework |
| `AgentConfig` | LLM設定の統一管理 | 環境変数 |
| `AssistantAgent` | 専門タスク実行 | MCP Tools |
| `GroupChatManager` | エージェント自動選択 | LLM (Ollama) |
| `MCPServer` | ツール実行エンドポイント | FastAPI, DuckDB |
| `MCP Tools` | HTTP通信 + フォールバック | httpx, MCP Server |
| `Phoenix Instrumentation` | トレーシング自動化 | OpenTelemetry |

---

## データフロー

### MCP統合データフロー

```text
User Natural Language Query
    │
    ▼
┌─────────────────────────────────┐
│      Streamlit UI (Python)      │
│  {"query": "顧客数を教えて"}      │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│   MultiAgentOrchestrator        │
│   orchestrator.execute(query)   │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│      GroupChatManager           │
│  LLM-based agent selection      │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│         SQL Agent               │
│  "I need to query customers"    │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│     MCP Tools (HTTP Client)     │
│  _call_mcp_tool("query", {...}) │
└─────────────────────────────────┘
    │
    │ HTTP POST
    ▼
┌─────────────────────────────────┐
│      MCP Server (FastAPI)       │
│  JSON-RPC Request Processing    │
│  {                              │
│    "jsonrpc": "2.0",            │
│    "method": "tools/call",      │
│    "params": {                  │
│      "name": "query",           │
│      "arguments": {             │
│        "query": "SELECT ..."    │
│      }                          │
│    }                            │
│  }                              │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│         DuckDB Engine           │
│  SQL: SELECT COUNT(*) FROM ...  │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│      Raw Query Result           │
│  [(200,)]                       │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│      MCP Server Response        │
│  {                              │
│    "jsonrpc": "2.0",            │
│    "result": {                  │
│      "content": [{              │
│        "type": "text",          │
│        "text": "[{...}]"        │
│      }]                         │
│    }                            │
│  }                              │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│     MCP Tools Formatter         │
│  _format_query_results()        │
│  "count\n-----\n200"            │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│         SQL Agent               │
│  "データベースには200件の..."     │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│      GroupChatManager           │
│  {                              │
│    "conversation": [...],       │
│    "agents": ["sql_agent"]      │
│  }                              │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│        Streamlit UI             │
│  st.chat_message("assistant")   │
│  "データベースには200件の..."     │
└─────────────────────────────────┘
```

### データ型の遷移

| ステージ | データ型 | 例 |
|---------|---------|---|
| User Input | `str` | "顧客数を教えて" |
| Orchestrator | `str` | (変更なし) |
| SQL Agent LLM | `str` (prompt) | "Get customer count from database" |
| MCP Tool Call | `dict` | `{"query": "SELECT COUNT(*) ..."}` |
| HTTP Request | JSON-RPC | `{"jsonrpc": "2.0", "method": "tools/call", ...}` |
| MCP Server | FastAPI Request | Pydantic model validation |
| DuckDB Query | SQL string | `SELECT COUNT(*) FROM customers` |
| DuckDB Result | `list[tuple]` | `[(200,)]` |
| MCP Response | JSON-RPC | `{"result": {"content": [...]}}` |
| Tool Formatter | `str` | `"count\n-----\n200"` |
| Agent Response | `str` | "データベースには200件の顧客..." |
| UI Display | Markdown | Rendered in Streamlit |

### Phoenix トレーシング (自動)

```python
# コード内で明示的な計装不要
from phoenix.otel import register

tracer_provider = register(
    project_name="ag2-multiagent-nl2sql",
    endpoint="http://phoenix:6006/v1/traces",
)
```

**自動収集される情報**:

- デコレーター不要（自動インストルメンテーション）
- LLM呼び出し（プロンプト、レスポンス、レイテンシ）
- エージェント会話履歴
- MCP HTTP通信ログ
- ツール実行時間
- エラーとスタックトレース

---

## エラーハンドリング

### MCP統合におけるエラー処理

#### 1. MCP通信エラー

```python
# mcp_tools/database.py
def _call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    try:
        response = httpx.post(mcp_url, json=request, timeout=30.0)
        response.raise_for_status()
        result = response.json()

        if "error" in result and result["error"]:
            raise RuntimeError(f"MCP error: {result['error']}")

        return result.get("result", {})

    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.warning(f"MCP server unavailable, using fallback: {e}")
        return _fallback_direct_query(arguments)
```

#### 2. SQLエラー

```python
# mcp_server/server.py
async def execute_query(request_id: int, arguments: dict[str, Any]) -> MCPResponse:
    try:
        query = arguments.get("query", "")
        conn = duckdb.connect(DB_PATH, read_only=READ_ONLY)
        result = conn.execute(query).fetchall()

        return MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            result={"content": [{"type": "text", "text": str(result)}]}
        )
    except Exception as e:
        return MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            error={"code": -32603, "message": f"Database error: {str(e)}"}
        )
```

#### 3. エージェント実行エラー

```python
# function/ag2_orchestrator.py
def execute(self, query: str) -> dict[str, Any]:
    try:
        self.group_chat.reset()
        self.user_proxy.initiate_chat(self.manager, message=query)

        return {
            "conversation": self._extract_conversation(),
            "agents": self._get_active_agents()
        }
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "conversation": [{"name": "system", "content": f"エラー: {str(e)}"}],
            "agents": []
        }
```

### エラー伝播フロー

```text
MCP Server Error
    │
    ▼
HTTP 500 Response
    │
    ▼
MCP Tools catches exception
    │
    ├──> Try fallback to direct DuckDB
    │    └──> Success: Return result
    │
    └──> Fallback failed: Return error message
         │
         ▼
SQL Agent receives error
    │
    ▼
LLM processes error context
    │
    ├──> Retry with corrected query
    │
    └──> Report error to user
         │
         ▼
GroupChatManager continues/terminates
    │
    ▼
Streamlit displays conversation (including errors)
```

---

## まとめ

### MCP統合の利点

1. **標準化**: JSON-RPC 2.0による統一ツールインターフェース
2. **拡張性**: MCPサーバーを独立してスケール可能
3. **可観測性**: HTTP通信による完全なログとトレース
4. **柔軟性**: 言語・フレームワークに非依存
5. **信頼性**: フォールバック機構による高可用性

### アーキテクチャの強み

1. **モジュール性**: 各コンポーネントが独立した責務を持つ
2. **セキュリティ**: サンドボックス化されたコード実行環境
3. **保守性**: 明確な責任分離と標準化されたインターフェース
4. **自動化**: 完全自動のLLMトレーシングとMCPロギング
5. **マイクロサービス**: MCPサーバーの独立デプロイと管理

### 開発時の注意点

- **pyautogenバージョン**: 必ず `0.2.35` を使用（0.3.0+は非互換）
- **MCP通信**: タイムアウト設定とフォールバック機構を維持
- **GroupChat max_round**: 複雑なクエリには増やす必要あり
- **ツールセキュリティ**: インポート・ファイルI/Oの制限を維持
- **エラーハンドリング**: MCP障害時の自動フォールバックを考慮

### 参考リンク

- [AG2 (AutoGen) Documentation](https://microsoft.github.io/autogen/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Phoenix (Arize AI) Documentation](https://docs.arize.com/phoenix/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
