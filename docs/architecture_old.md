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

#### クラス構成

##### AgentConfig

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

##### MultiAgentOrchestrator

```python
class MultiAgentOrchestrator:
    """メインオーケストレータクラス"""

    def __init__(self, model: str | None = None,
                 base_url: str | None = None,
                 work_dir: Path | None = None):
        # 1. 設定初期化
        config = AgentConfig(model, base_url)

        # 2. 専門エージェント作成
        self.sql_agent = create_sql_agent(config)
        self.web_agent = create_web_agent(config)
        self.reasoning_agent = create_reasoning_agent(config, work_dir)

        # 3. ユーザープロキシ作成
        self.user_proxy = UserProxyAgent(
            name="user",
            human_input_mode="NEVER",  # 自動実行
            code_execution_config=False,
        )

        # 4. GroupChat設定
        self.group_chat = GroupChat(
            agents=[self.user_proxy, self.sql_agent,
                   self.web_agent, self.reasoning_agent],
            messages=[],
            max_round=10,
            speaker_selection_method="auto",  # 自動選択
        )

        # 5. GroupChatManager作成
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=config.llm_config,
        )
```

**主要メソッド**:

```python
def execute(self, query: str) -> dict[str, Any]:
    """クエリを実行してエージェント会話を取得

    Args:
        query: ユーザーからの自然言語クエリ

    Returns:
        {
            "conversation": [{"name": "agent_name", "content": "..."}],
            "agents": ["sql_agent", "web_agent"]
        }
    """
    self.group_chat.reset()  # 会話履歴クリア
    self.user_proxy.initiate_chat(self.manager, message=query)

    # 会話履歴の抽出・整形
    conversation = [
        {"name": msg.get("name", "unknown"),
         "content": msg.get("content", "")}
        for msg in self.group_chat.messages
        if msg.get("content")
    ]

    return {
        "conversation": conversation,
        "agents": list(set(msg["name"] for msg in conversation
                          if msg["name"] != "user"))
    }
```

---

### 3. 専門エージェント

#### SQL Agent (`create_sql_agent`)

**目的**: データベースクエリの専門家

**システムメッセージ**:
```python
"""You are a SQL specialist.
Analyze database schemas and generate SQL queries.
Use get_database_schema to understand table structures.
Use execute_sql_query to run queries.
"""
```

**登録ツール**:
```python
tools = create_database_tools()
sql_agent.register_function(function_map=tools)
```

**動作フロー**:

1. ユーザークエリを受信
2. `get_database_schema()` でスキーマ確認 (MCP経由)
3. SQL生成
4. `execute_sql_query()` で実行 (MCP経由)
5. 結果を自然言語で要約

#### Web Agent (`create_web_agent`)

**目的**: Web情報収集の専門家

**システムメッセージ**:

```python
"""You are a web research specialist.
Search the web and scrape content to gather information.
Use web_search for finding relevant pages.
Use scrape_webpage to extract detailed content.
"""
```

**登録ツール**:

```python
tools = create_web_tools()
web_agent.register_function(function_map=tools)
```

**動作フロー**:

1. 検索クエリを受信
2. `web_search()` でDuckDuckGo検索
3. 関連URLから `scrape_webpage()` でコンテンツ抽出
4. 情報を統合・要約

#### Reasoning Agent (`create_reasoning_agent`)

**目的**: データ分析・予測の専門家

**システムメッセージ**:

```python
"""You are a data analyst specializing in predictions.
Perform statistical analysis and forecasting.
Use python_interpreter for calculations.
Write clean, documented code.
"""
```

**登録ツール**:

```python
tools = create_interpreter_tool()
reasoning_agent.register_function(function_map=tools)

# コード実行環境
executor = LocalCommandLineCodeExecutor(work_dir=work_dir)
reasoning_agent.register_for_execution(code_executor=executor)
```

**動作フロー**:

1. 分析要求を受信
2. Pythonコード生成
3. `python_interpreter()` でサンドボックス実行
4. 結果を可視化・解説

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

## データフロー

### MCP統合データフロー

```python
def create_database_tools() -> dict[str, Callable]:
    """データベースツールの作成"""

    def get_database_schema(query: str = "") -> str:
        """テーブルスキーマ取得

        Returns:
            "Table: customers (200 rows)\n..."
        """
        conn = duckdb.connect(DATABASE_PATH)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()

        result = []
        for table in tables:
            row_count = conn.execute(
                f"SELECT COUNT(*) FROM {table[0]}"
            ).fetchone()[0]
            result.append(f"Table: {table[0]} ({row_count} rows)")

        return "\n".join(result)

    def execute_sql_query(sql: str) -> str:
        """SQL実行（最大50行）

        Args:
            sql: 実行するSQLクエリ

        Returns:
            フォーマット済み結果テーブル
        """
        conn = duckdb.connect(DATABASE_PATH)
        df = conn.execute(sql).df()
        return df.head(50).to_string()

    return {
        "get_database_schema": get_database_schema,
        "execute_sql_query": execute_sql_query,
    }
```

#### Web Tools (`web.py`)

```python
def create_web_tools() -> dict[str, Callable]:
    """Web検索・スクレイピングツール"""

    def web_search(query: str) -> str:
        """DuckDuckGo検索（上位5件）"""
        results = DDGS().text(query, max_results=5)
        return json.dumps(results, ensure_ascii=False)

    def scrape_webpage(url: str) -> str:
        """Webページのコンテンツ抽出（2000文字制限）"""
        response = httpx.get(url, timeout=10.0)
        soup = BeautifulSoup(response.text, "html.parser")

        # script/styleタグ削除
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text()
        return text[:2000]

    return {
        "web_search": web_search,
        "scrape_webpage": scrape_webpage,
    }
```

#### Interpreter Tool (`interpreter.py`)

```python
ALLOWED_IMPORTS = {'math', 'statistics', 'datetime', 'json', 're'}

def create_interpreter_tool() -> dict[str, Callable]:
    """安全なPythonインタープリタ"""

    def python_interpreter(code: str) -> str:
        """サンドボックス環境でコード実行

        Security:
            - ホワイトリストインポートのみ許可
            - ファイルI/O禁止
            - ネットワークアクセス禁止
            - システムコール禁止
        """
        # AST解析でインポートチェック
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] not in ALLOWED_IMPORTS:
                        raise ValueError(f"Import not allowed: {alias.name}")

        # 制限付き環境で実行
        namespace = {"__builtins__": {}}
        exec(code, namespace)

        return str(namespace.get("result", "No result"))

    return {"python_interpreter": python_interpreter}
```

---

## モジュール間通信フロー

### 1. ユーザークエリ受信

```text
User Input: "2024年で最も売れた商品は？"
    ↓
Streamlit UI: st.chat_input()
    ↓
Session State: messages.append({"role": "user", ...})
    ↓
Orchestrator: execute(query)
```

### 2. エージェント選択

```text
GroupChatManager.initiate_chat()
    ↓
speaker_selection_method="auto"
    ↓
LLM判断: "SQL Agentが適切"
    ↓
SQL Agent.receive(message)
```

**選択ロジック**:
- GroupChatManagerがLLMを使用して最適なエージェントを選択
- 各エージェントの `system_message` を元に判断
- 文脈に応じて動的に切り替え

### 3. ツール実行

```text
SQL Agent
    ↓
"get_database_schema を呼び出します"
    ↓
function_map["get_database_schema"]()
    ↓
DuckDB: SELECT table_name FROM information_schema.tables
    ↓
Result: "Table: customers (200 rows)\n..."
    ↓
SQL Agent: スキーマを元にSQL生成
    ↓
"execute_sql_query を呼び出します"
    ↓
DuckDB: SELECT product_name, COUNT(*) ...
    ↓
Result: DataFrame(50 rows max)
    ↓
SQL Agent: 結果を自然言語で要約
```

### 4. 結果返却

```text
SQL Agent: 最終回答生成
    ↓
GroupChat.messages.append({...})
    ↓
Orchestrator.execute() → return conversation
    ↓
Streamlit UI: st.chat_message("assistant")
    ↓
User Browser: 回答表示
```

### 5. テレメトリ

```text
全オペレーション(自動インストルメンテーション)
    ↓
OpenTelemetry SDK
    ↓
OTLP gRPC: Phoenix Collector (port 4317)
    ↓
Phoenix Server
    ↓
SQLite: トレースデータ永続化
    ↓
Phoenix UI: トレース可視化 (http://localhost:6006)
```

**特徴**:
- デコレーター不要（自動インストルメンテーション）
- APIキー不要
- リアルタイムトレース表示
- LLMコール、エージェント会話、ツール実行の完全な可視化

---

## クラス設計

### クラス図

```text
┌─────────────────────────────┐
│     MultiAgentOrchestrator  │
├─────────────────────────────┤
│ - config: AgentConfig       │
│ - sql_agent: AssistantAgent │
│ - web_agent: AssistantAgent │
│ - reasoning_agent: Agent    │
│ - user_proxy: UserProxyAgent│
│ - group_chat: GroupChat     │
│ - manager: GroupChatManager │
├─────────────────────────────┤
│ + execute(query: str)       │
│   → dict[str, Any]          │
└─────────────────────────────┘
           │ uses
           ▼
┌─────────────────────────────┐
│       AgentConfig           │
├─────────────────────────────┤
│ + llm_config: dict          │
├─────────────────────────────┤
│ + __init__(model, base_url) │
└─────────────────────────────┘

┌─────────────────────────────┐
│     AssistantAgent          │
│     (AG2 Framework)         │
├─────────────────────────────┤
│ + name: str                 │
│ + system_message: str       │
│ + llm_config: dict          │
├─────────────────────────────┤
│ + register_function()       │
│ + receive(message)          │
└─────────────────────────────┘
           △
           │ inherits
    ┌──────┴──────────┬────────────┐
    │                 │            │
┌───────┐      ┌──────────┐   ┌────────────┐
│SQL    │      │Web       │   │Reasoning   │
│Agent  │      │Agent     │   │Agent       │
└───────┘      └──────────┘   └────────────┘

┌─────────────────────────────┐
│      GroupChatManager       │
│      (AG2 Framework)        │
├─────────────────────────────┤
│ + groupchat: GroupChat      │
│ + llm_config: dict          │
├─────────────────────────────┤
│ + run()                     │
│ + select_speaker()          │
└─────────────────────────────┘
```

### 依存関係

```text
ui/app.py
    → ag2_orchestrator.MultiAgentOrchestrator
        → autogen.AssistantAgent (×3)
        → autogen.UserProxyAgent
        → autogen.GroupChat
        → autogen.GroupChatManager
        → mcp_tools.database
        → mcp_tools.web
        → mcp_tools.interpreter

mcp_tools/*
    → duckdb (database.py)
    → httpx, beautifulsoup4 (web.py)
    → ast (interpreter.py)
```

---

## データフロー

### エンドツーエンドデータフロー

```text
1. Input Phase
   User: "顧客数を教えて"
   ↓
   Streamlit: query string
   ↓
   Orchestrator: execute(query)

2. Agent Selection Phase
   GroupChatManager
   ↓
   LLM Decision: "SQL Agent"
   ↓
   SQL Agent activates

3. Tool Invocation Phase
   SQL Agent
   ↓
   Tool Call: get_database_schema()
   ↓
   DuckDB Query: SELECT table_name ...
   ↓
   Result: "customers (200 rows)"
   ↓
   Tool Call: execute_sql_query("SELECT COUNT(*) FROM customers")
   ↓
   Result: "200"

4. Response Generation Phase
   SQL Agent
   ↓
   LLM Generation: "顧客数は200人です"
   ↓
   GroupChat.messages append

5. Output Phase
   Orchestrator
   ↓
   Return: {conversation: [...], agents: ["sql_agent"]}
   ↓
   Streamlit
   ↓
   User Browser: Display response
```

### データ変換パイプライン

```text
Natural Language Query
    ↓ (Streamlit)
str
    ↓ (Orchestrator)
GroupChat Message
    ↓ (GroupChatManager)
Agent Selection
    ↓ (Agent)
Tool Function Call
    ↓ (MCP Tools)
SQL Query / HTTP Request / Python Code
    ↓ (External System)
Raw Data (DataFrame / HTML / Calculation Result)
    ↓ (Tool Function)
Formatted String
    ↓ (Agent)
Natural Language Response
    ↓ (Orchestrator)
dict[str, Any]
    ↓ (Streamlit)
HTML/Markdown
    ↓ (Browser)
Rendered UI
```

---

## エラーハンドリング

### エラータイプと対処

#### 1. LLM接続エラー

```python
# ag2_orchestrator.py
try:
    self.user_proxy.initiate_chat(self.manager, message=query)
except Exception as e:
    logger.error(f"Agent execution failed: {e}")
    return {
        "conversation": [{"name": "system",
                         "content": f"エラー: {str(e)}"}],
        "agents": []
    }
```

#### 2. ツール実行エラー

```python
# mcp_tools/database.py
def execute_sql_query(sql: str) -> str:
    try:
        conn = duckdb.connect(DATABASE_PATH)
        df = conn.execute(sql).df()
        return df.head(50).to_string()
    except Exception as e:
        return f"SQL実行エラー: {str(e)}"
```

#### 3. インポートセキュリティエラー

```python
# mcp_tools/interpreter.py
def python_interpreter(code: str) -> str:
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base = alias.name.split('.')[0]
                    if base not in ALLOWED_IMPORTS:
                        raise ValueError(f"許可されていないインポート: {alias.name}")
        # ... execution
    except Exception as e:
        return f"実行エラー: {str(e)}"
```

### エラー伝播フロー

```text
Tool Error
    ↓
Return error string to Agent
    ↓
Agent LLM processes error
    ↓
Either:
  - Retry with corrected input
  - Report error to user
    ↓
GroupChat continues or terminates
    ↓
Orchestrator returns conversation
    ↓
Streamlit displays (including errors)
```

---

## まとめ

### アーキテクチャの強み

1. **モジュール性**: 各エージェントが独立した責務を持つ
2. **拡張性**: 新しいエージェント・ツールの追加が容易
3. **安全性**: サンドボックス化されたコード実行環境
4. **可観測性**: 全オペレーションがトレース可能
5. **保守性**: 明確な責任分離と標準化されたインターフェース

### 開発時の注意点

- **pyautogenバージョン**: 必ず `<0.3.0` を使用（0.10.0は非互換）
- **GroupChat max_round**: 複雑なクエリには増やす必要あり
- **ツールセキュリティ**: インポート・ファイルI/Oの制限を維持
- **LLMモデル選択**: 日本語対応と推論能力のバランスを考慮
- **エラーハンドリング**: エージェント間でのエラー伝播を考慮した設計

### 参考リンク

- [AG2 (AutoGen) Documentation](https://microsoft.github.io/autogen/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Phoenix (Arize AI) Documentation](https://docs.arize.com/phoenix/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
