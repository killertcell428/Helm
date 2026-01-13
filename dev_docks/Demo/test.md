
### やりたいことの整理

- 今の Helm の **評価ロジック／LLM の精度／出力内容** を、
- **仮の会議ログ・議事録・チャット履歴**をいくつか用意して、
- **ブラウザ上から入力 → LLM に評価させて結果を見る**、という形で確認したい

この目的には、既にある **FastAPI の API ドキュメント（Swagger UI）** を使うのが一番早いです。
`/api/meetings/ingest`, `/api/chat/ingest`, `/api/analyze` は、すべてブラウザから任意のテキストを投げられます。

---

### 1. バックエンドを起動

PowerShell で（パスは既にこのプロジェクト直下だと仮定）:

```powershell
cd Dev\backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- すでに環境構築済みなら、`uvicorn ...` だけでOKです。

---

### 2. ブラウザから Swagger UI を開く

- ブラウザで `http://localhost:8000/docs` を開く
- ここから以下の順で API を叩きます（全部ブラウザ内で完結します）：

1. `/api/meetings/ingest` に議事録を投げる
2. `/api/chat/ingest` にチャットログを投げる
3. `/api/analyze` でその組み合わせを評価させる

---

### 3. パターン別のダミーデータ例

以下、そのまま Swagger UI の「Example Value」のところに貼り替えれば使える JSON です。
`meeting_id` / `chat_id` をパターンごとに変えることで、何パターンでも保存→分析できます。

#### パターンA: 典型的な「正当化フェーズ」強め（B1_正当化フェーズを狙う）

**1) 議事録取り込み (`POST /api/meetings/ingest`)**

```json
{
  "meeting_id": "demo_meeting_A",
  "transcript": "CFO: モバイルARPUは前年同期比▲7.5%で、3四半期連続の下方修正です。\nCFO: 5G設備投資は当初計画比＋20%となっており、減価償却負担が増加しています。\nCFO: DX事業の営業利益率は▲15%で、前回会議からさらに悪化しています。\nCEO: 数字は厳しいが、我々の中長期戦略は正しい方向だと思う。\nCEO: 今は我慢の時期。計画は維持しつつ、各本部でコストの工夫をお願いしたい。\n通信本部長: ARPU低下は市場要因も大きく、短期では打てる手が限られる状況です。\nDX本部長: ここで投資を減らすと将来の成長機会を逃します。今は仕込みを続けるべきです。\nCEO: では、2025年度計画は現行のまま維持する方向で。詳細は各本部で詰めてください。\n結論: 2025年度計画は維持。各本部はコスト最適化案を検討。次回進捗報告は3か月後。",
  "metadata": {
    "meeting_name": "四半期経営会議（パターンA）",
    "date": "2025-02-01",
    "participants": ["CFO", "CEO", "通信本部長", "DX本部長"]
  }
}
```

**2) チャット取り込み (`POST /api/chat/ingest`)**

```json
{
  "chat_id": "demo_chat_A",
  "messages": [
    {
      "user": "経営企画A",
      "text": "正直、この数字で何も方向性を変えないのは危険だと思います…",
      "timestamp": "2025-02-01T15:30:00Z"
    },
    {
      "user": "経営企画B",
      "text": "やめた方がいいプロジェクトもそろそろ整理しないと、現場がもたないですね。",
      "timestamp": "2025-02-01T15:32:00Z"
    },
    {
      "user": "通信本部補佐",
      "text": "撤退案を口に出す空気ではまったくなかったですね。次回も同じ話になりそうです。",
      "timestamp": "2025-02-01T15:35:00Z"
    }
  ],
  "metadata": {
    "channel_name": "経営企画チャンネル（パターンA）",
    "project_id": "project_zombie_A"
  }
}
```

**3) 構造分析 (`POST /api/analyze`)**

```json
{
  "meeting_id": "demo_meeting_A",
  "chat_id": "demo_chat_A"
}
```

- このパターンでは、
  - KPI 下方修正の言及が複数回
  - 「撤退」「ピボット」などが会議内では一切出てこない
  - チャットで反対/懸念が出ている
    ので、`B1_正当化フェーズ` が **HIGH スコア・高重要度/高緊急度** になりやすい設計です。

---

#### パターンB: 撤退・ピボット議論あり（健全な議論、スコア低めを狙う）

**1) 議事録 (`/api/meetings/ingest`)**

```json
{
  "meeting_id": "demo_meeting_B",
  "transcript": "CFO: モバイルARPUは前年同期比▲3.0%ですが、直近は横ばい傾向です。\nCFO: DX事業の利益率は▲5%で、前四半期からは少し改善しています。\nCEO: 現行戦略を続ける前提でいいのか、一度撤退も含めて3案を比較したい。\nCEO: 継続、縮小、撤退の3つのオプションを次回までに整理してください。\n通信本部長: 一部地域では撤退した方がいい可能性もあります。データを出します。\nDX本部長: 既存プロダクトの中止も含めて案を出します。\n結論: 次回会議で『継続・縮小・撤退』の3案比較を実施。撤退案のドラフトはDX本部長が担当。",
  "metadata": {
    "meeting_name": "四半期経営会議（パターンB）",
    "date": "2025-02-08",
    "participants": ["CFO", "CEO", "通信本部長", "DX本部長"]
  }
}
```

**2) チャット (`/api/chat/ingest`)**

```json
{
  "chat_id": "demo_chat_B",
  "messages": [
    {
      "user": "経営企画A",
      "text": "撤退案まで含めて議論する流れになったのはかなり大きいですね。",
      "timestamp": "2025-02-08T15:30:00Z"
    },
    {
      "user": "DX本部長",
      "text": "さっきの会議内容はExecutiveにも共有済みです。正式なエスカレーションとして扱います。",
      "timestamp": "2025-02-08T15:35:00Z"
    }
  ],
  "metadata": {
    "channel_name": "経営企画チャンネル（パターンB）",
    "project_id": "project_zombie_B"
  }
}
```

**3) 構造分析 (`/api/analyze`)**

```json
{
  "meeting_id": "demo_meeting_B",
  "chat_id": "demo_chat_B"
}
```

- このパターンでは `exit_discussed = True` になりやすく、
  「やめる選択肢」がちゃんと議論されているので、
  **B1_正当化フェーズのスコアが低い or 検出されない** 挙動が期待されます。

---

#### パターンC: リスクは出ているが報告・エスカレーションが曖昧（ES1_報告遅延を狙う）

**1) 議事録 (`/api/meetings/ingest`)**

```json
{
  "meeting_id": "demo_meeting_C",
  "transcript": "CFO: 今期のKPIは一部未達ですが、全体では計画レンジ内です。\nCEO: 今日は主に進捗確認だけにしましょう。大きな戦略変更は扱いません。\n通信本部長: 一部プロジェクトで障害リスクが高まっていますが、詳細は持ち帰ります。\nDX本部長: その件はチーム内で検討を進めておきます。\n結論: 現状維持。リスク詳細は次回以降のアジェンダ候補とする。",
  "metadata": {
    "meeting_name": "定例進捗会議（パターンC）",
    "date": "2025-02-10",
    "participants": ["CFO", "CEO", "通信本部長", "DX本部長"]
  }
}
```

**2) チャット (`/api/chat/ingest`)**

```json
{
  "chat_id": "demo_chat_C",
  "messages": [
    {
      "user": "開発リーダー",
      "text": "このまま進めると障害リスクがかなり高いです。止める判断を上に上げた方がいいと思います。",
      "timestamp": "2025-02-10T13:00:00Z"
    },
    {
      "user": "プロジェクトマネージャー",
      "text": "ですよね…ただ今会議に出すと揉めそうなので、もう少し様子を見ましょう。",
      "timestamp": "2025-02-10T13:05:00Z"
    }
  ],
  "metadata": {
    "channel_name": "プロジェクトチャット（パターンC）",
    "project_id": "project_risk_C"
  }
}
```

**3) 構造分析 (`/api/analyze`)**

```json
{
  "meeting_id": "demo_meeting_C",
  "chat_id": "demo_chat_C"
}
```

- ここでは、
  - チャットで「やばい」「止める」「上げた方がいい」系のリスクワードが出ている
  - しかし会議内でははっきりエスカレーションされていない
- ので、`ES1_報告遅延` が **MEDIUM くらいのスコア** で出るシナリオを想定しています。

---

### 4. LLM（Gemini）を使うかどうか

- `.env` に `USE_LLM=true` ＋ `GOOGLE_API_KEY` などが入っていれば、`/api/analyze` は **LLM + ルール** を使い、レスポンスに:
  - `is_llm_generated: true`
  - `llm_status: "success"`
    などが付きます。
- 未設定なら rule ベースのみで、`is_llm_generated: false`, `llm_status: "mock_fallback"` になります。

---

### 5. 何を見ると「ロジック・精度・出力」が分かるか

- `/api/analyze` レスポンスの中の:
  - **`findings[]`**: どのパターンID（`B1_正当化フェーズ`, `ES1_報告遅延` など）が出たか
  - **`overall_score`, `severity`, `urgency`**: 全体のスコア・重要度・緊急度
  - **`findings[].quantitative_scores`**: KPI下方修正回数・判断集中率などの数値
  - **`explanation`**: Executive 向けの日本語サマリー
- これをパターンA/B/Cで見比べると、「どういう入力に対して、どんな表／ロジック／スコア／説明になるか」がかなりクリアに見えるはずです。

---

もし「Swagger ではなく、Next.js の画面からテキストを直接貼って試したい」という形にしたければ、
`/api/analyze` へ直接投げるサンドボックスページ（テキストエリア＋結果表示）をフロント側に1ページ増やす案もあります。
その実装まで進めたい場合は、どの UI イメージか（単純にテキスト2つ＋ボタンでOKか）だけ教えてもらえれば、そこまで組み込みます。
