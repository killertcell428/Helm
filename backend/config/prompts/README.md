# LLMプロンプト定義

組織グラフ・RACIと同様に、LLM用の指示（プロンプト）をヒトが変更しやすいようにファイルで管理しています。

## ディレクトリ構成

```
config/prompts/
├── analysis/                    # マルチ視点分析用
│   ├── base.txt                 # 共通テンプレート（変数: role_description, meeting_transcript, chat_messages, materials_content, analysis_points）
│   ├── role_executive.txt       # CEO視点の役割説明
│   ├── role_staff.txt           # 現場視点の役割説明
│   ├── role_corp_planning.txt    # 経営企画視点の役割説明
│   ├── role_governance.txt       # ガバナンス視点の役割説明
│   ├── role_default.txt         # 未定義ロール用
│   ├── analysis_points_*.txt     # 各ロールの分析観点（健全/問題の判断基準）
│   └── analysis_points_default.txt
├── task_generation.txt          # タスク生成用（変数: analysis_result_json, decision, modifications, interventions）
├── agents/                      # ADKエージェント用
│   ├── research_instruction.txt # ResearchAgent の system instruction
│   ├── research_prompt.txt      # 実行時の user prompt テンプレート（{topic}）
│   ├── analysis_instruction.txt
│   ├── analysis_prompt.txt      # {description}
│   ├── notification_instruction.txt
│   └── notification_prompt.txt  # {recipients}, {document_url}, {description}
└── README.md
```

## 変更方法

1. 該当する `.txt` ファイルを編集
2. アプリを再起動（プロンプトは起動時に読み込まれる）
3. ファイルが存在しない・読み込み失敗時は、コード内のフォールバックが使用される

## 変数（プレースホルダ）

- `{role_description}`: ロール説明
- `{meeting_transcript}`: 会議議事録
- `{chat_messages}`: チャットログ
- `{materials_content}`: 会議資料
- `{analysis_points}`: ロール別分析観点
- `{analysis_result_json}`: 分析結果（JSON）
- `{decision}`, `{modifications}`, `{interventions}`: 承認内容
- `{topic}`, `{description}`: エージェント実行時の入力
- `{recipients}`, `{document_url}`: 通知エージェント用
