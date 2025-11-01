# Open WebUI セットアップガイド

## NL2SQL Function の登録方法

### 1. Open WebUI にアクセス

ブラウザで http://localhost:3000 を開きます。

### 2. 管理画面にアクセス

1. 右上のユーザーアイコンをクリック
2. **Admin Panel** または **設定** を選択

### 3. Functions の設定

1. 左側のメニューから **Functions** を選択
2. 右上の **+ Add Function** ボタンをクリック
3. **Function URL** に以下を入力:
   ```
   http://nl2sql-function:8000
   ```

   > **注意**: Docker ネットワーク内のサービス名 `nl2sql-function` を使用します。
   > ホストから `http://localhost:8001` でアクセスできても、Open WebUI コンテナ内からは `http://nl2sql-function:8000` でアクセスする必要があります。

4. **Test Connection** をクリックして接続を確認
5. 接続が成功したら **Save** をクリック

### 4. Function の有効化

1. Functions リストに **NL2SQL Database Query Agent** が表示されます
2. トグルスイッチをオンにして有効化

### 5. チャットで使用

1. 新しいチャットを開始
2. モデル選択メニューで Ollama モデル (gemma2:2b-instruct-q4_K_M) を選択
3. 右側の **Functions** タブまたはアイコンをクリック
4. **NL2SQL Database Query Agent** を有効化
5. 日本語で質問を入力:
   - 「顧客数を教えて」
   - 「2024年で最も売れた商品は？」
   - 「東京都の顧客は何人？」
   - 「注文金額が高い顧客トップ5を教えて」

## トラブルシューティング

### Function が表示されない

1. Function サービスが起動しているか確認:
   ```bash
   docker ps | grep nl2sql-function
   ```

2. Function のログを確認:
   ```bash
   docker logs nl2sql-function
   ```

3. エンドポイントが応答するか確認:
   ```bash
   curl http://localhost:8001/info
   ```

### 接続エラーが発生する

1. Docker ネットワークを確認:
   ```bash
   docker network inspect nl2sql-agent_nl2sql-network
   ```

2. Open WebUI から Function サービスに到達できるか確認:
   ```bash
   docker exec nl2sql-open-webui curl http://nl2sql-function:8000/health
   ```

3. URL を確認 (コンテナ内では `nl2sql-function:8000` を使用)

### データベースに接続できない

1. データベースファイルが存在するか確認:
   ```bash
   docker exec nl2sql-function ls -la /app/data/ecommerce.db
   ```

2. データベースが初期化されているか確認:
   ```bash
   docker exec nl2sql-function python /app/data/setup_database.py
   ```

## 動作確認済みクエリ例

### 基本クエリ
- 顧客数を教えて
- 商品数は？
- 注文の合計件数を教えて

### 集計クエリ
- 2024年の注文総額は？
- 最も売れた商品トップ3を教えて
- カテゴリ別の売上を教えて

### フィルタリングクエリ
- 東京都の顧客数は？
- 電化製品で在庫が10個以下の商品は？
- 2024年10月の注文数は？

### 複雑なクエリ
- 注文金額が最も高い顧客トップ10を教えて
- 都道府県別の顧客数ランキングを教えて
- 商品別の平均注文単価を教えて
