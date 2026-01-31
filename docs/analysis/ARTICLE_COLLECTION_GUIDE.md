# 受賞記事収集ガイド

## 目的
各受賞記事の内容を効率的に取得・テキスト化するための手順書

## 収集方法の選択肢

### 方法1: ブラウザ拡張機能を使用（推奨）

#### Chrome拡張機能
1. **MarkDownload - Markdown Web Clipper**
   - インストール: Chrome Web Store
   - 使用方法: 記事ページで拡張機能を起動 → Markdown形式で保存
   - メリット: 画像も含めてMarkdown形式で保存可能

2. **SingleFile**
   - インストール: Chrome Web Store
   - 使用方法: 記事ページで拡張機能を起動 → HTML形式で保存
   - メリット: 完全なページを1ファイルで保存

#### Firefox拡張機能
1. **SingleFile**
   - 同様にFirefox版も利用可能

### 方法2: ブラウザの開発者ツールを使用

1. 記事ページを開く
2. F12で開発者ツールを開く
3. Consoleタブで以下を実行:

```javascript
// 記事本文を取得
const article = document.querySelector('article');
const title = document.querySelector('h1')?.textContent || 'タイトル不明';
const content = article?.innerText || document.body.innerText;

// Markdown形式で出力
console.log(`# ${title}\n\n${content}`);
```

4. コンソール出力をコピーしてテキストファイルに保存

### 方法3: Pythonスクリプトを使用（自動化）

```python
import requests
from bs4 import BeautifulSoup
import markdownify

def fetch_zenn_article(url):
    """Zenn記事を取得してMarkdown形式に変換"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 記事本文を取得
    article = soup.find('article')
    if article:
        # Markdown形式に変換
        md = markdownify.markdownify(str(article), heading_style="ATX")
        return md
    return None

# 使用例
urls = [
    'https://zenn.dev/nayus/articles/82e226cac28e53',
    'https://zenn.dev/gakkoudayoriai/articles/d7c61ec828913d',
    # ... 他のURL
]

for url in urls:
    content = fetch_zenn_article(url)
    if content:
        filename = url.split('/')[-1] + '.md'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
```

### 方法4: AIツールを活用

1. **Claude/GPT-4のURL読み込み機能**
   - 記事URLを直接入力
   - 「この記事をMarkdown形式でテキスト化してください」と依頼

2. **ChatGPT Code Interpreter**
   - URLを指定して記事を取得
   - Markdown形式で出力

## 画像の処理方法

### 画像の取得
1. 記事ページで画像を右クリック → 「名前を付けて画像を保存」
2. 画像ファイル名を記事内の位置と対応付けて管理

### 画像のテキスト化
1. **Google Lens**を使用
   - 画像をアップロード
   - テキストを抽出

2. **OCRツール**を使用
   - Tesseract OCR
   - Cloud Vision API

3. **手動で記述**
   - 画像の内容を文章で説明
   - 図表の場合は構造をテキストで記録

### 画像情報の記録フォーマット

```markdown
## 画像情報

### 画像1: システムアーキテクチャ図
- 位置: 「ソリューション設計」セクション
- ファイル名: architecture_diagram.png
- 内容: 
  - フロントエンド（Next.js）とバックエンド（FastAPI）の構成
  - Google Workspace APIとの連携
  - データフロー（議事録 → 分析 → アラート）
- テキスト化: [画像内のテキストをここに記述]

### 画像2: UIスクリーンショット
- 位置: 「UI/UX設計」セクション
- ファイル名: ui_screenshot.png
- 内容: デモページのスクリーンショット
  - 左側: プロジェクト一覧
  - 右側: 詳細情報表示
  - カラーパレット: 青系のグラデーション
```

## 収集した記事の保存構造

```
Dev/docs/analysis/award_articles/
├── vol2/
│   ├── 01_最優秀賞_FlatJam.md
│   ├── 01_最優秀賞_FlatJam_images/
│   │   ├── image1_architecture.png
│   │   └── image2_ui.png
│   ├── 02_2位_学校だよりAI.md
│   ├── 02_2位_学校だよりAI_images/
│   ├── 03_3位_VibePlanning.md
│   ├── 03_3位_VibePlanning_images/
│   ├── 04_TechDeepDive_SmartTwinRoom.md
│   ├── 05_Moonshot_KnockAI.md
│   └── 06_Firebase_AIMeeBo.md
├── vol3/
│   └── (vol3の記事)
└── analysis_results/
    ├── comparison_table.md
    ├── common_patterns.md
    └── helm_article_structure_proposal.md
```

## 記事テキスト化のチェックリスト

各記事について以下を確認:

- [ ] タイトルと著者情報
- [ ] すべての見出し（H1-H6）
- [ ] 本文のすべての段落
- [ ] コードブロック（言語指定含む）
- [ ] リスト（箇条書き、番号付き）
- [ ] リンク（URLとアンカーテキスト）
- [ ] 引用ブロック
- [ ] 画像の説明（キャプション）
- [ ] 画像内のテキスト（可能な限り）
- [ ] 表の内容（Markdown形式で）

## 効率化のコツ

1. **バッチ処理**: 複数の記事を一度に処理
2. **テンプレート使用**: 同じフォーマットで保存
3. **自動化スクリプト**: Pythonスクリプトで自動取得
4. **チェックリスト**: 漏れを防ぐ

## 注意事項

- Zennの利用規約を遵守
- 記事の著作権を尊重
- 分析目的での使用に留める
- 公開する場合は引用元を明記
