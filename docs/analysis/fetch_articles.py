"""
Zenn記事を取得してMarkdown形式で保存するスクリプト
"""
import requests
from bs4 import BeautifulSoup
import markdownify
import os
import time
from pathlib import Path

def fetch_zenn_article(url, output_dir="award_articles"):
    """
    Zenn記事を取得してMarkdown形式に変換
    
    Args:
        url: Zenn記事のURL
        output_dir: 出力ディレクトリ
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # タイトルを取得
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "タイトル不明"
        
        # 記事本文を取得
        article = soup.find('article')
        if not article:
            # フォールバック: メインコンテンツを探す
            article = soup.find('main') or soup.find('div', class_='article')
        
        if article:
            # Markdown形式に変換
            md_content = markdownify.markdownify(
                str(article),
                heading_style="ATX",
                bullets="-"
            )
            
            # メタデータを追加
            full_content = f"""# {title}

**URL**: {url}
**取得日**: {time.strftime('%Y-%m-%d %H:%M:%S')}

---

{md_content}
"""
            
            # ファイル名を生成（URLの最後の部分を使用）
            filename = url.split('/')[-1] + '.md'
            filename = filename.replace('?', '_').replace('&', '_')
            
            # 出力ディレクトリを作成
            os.makedirs(output_dir, exist_ok=True)
            
            # ファイルに保存
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            print(f"✓ Saved: {output_path}")
            return output_path
        else:
            print(f"✗ Article content not found: {url}")
            return None
            
    except Exception as e:
        print(f"✗ Error fetching {url}: {str(e)}")
        return None

def main():
    """メイン処理"""
    
    # vol2の受賞記事URL
    vol2_articles = [
        {
            'url': 'https://zenn.dev/nayus/articles/82e226cac28e53',
            'rank': '最優秀賞',
            'name': 'FlatJam',
            'team': 'IBUKI'
        },
        {
            'url': 'https://zenn.dev/gakkoudayoriai/articles/d7c61ec828913d',
            'rank': '2位',
            'name': '学校だよりAI',
            'team': 'わきAIAI@AI木曜会'
        },
        {
            'url': 'https://zenn.dev/huku/articles/e1addc5cf3837c',
            'rank': '3位',
            'name': 'Vibe Planning',
            'team': 'Vibe Coders'
        },
        {
            'url': 'https://zenn.dev/yumabo/articles/21cf9234d07328',
            'rank': 'Tech Deep Dive賞',
            'name': 'Smart Twin Room',
            'team': '個人'
        },
        {
            'url': 'https://zenn.dev/enostech/articles/8a4a3f2589afd7',
            'rank': 'Moonshot賞',
            'name': 'KnockAI',
            'team': 'KnockAI'
        },
        {
            'url': 'https://zenn.dev/marcosan/articles/80c0b704e88191',
            'rank': 'Firebase賞',
            'name': 'AIMeeBo',
            'team': '個人'
        },
    ]
    
    # vol3の記事URL（要確認）
    vol3_articles = [
        # TODO: vol3の受賞記事URLを追加
    ]
    
    # vol2の記事を取得
    print("=" * 60)
    print("Fetching vol2 articles...")
    print("=" * 60)
    
    vol2_dir = "award_articles/vol2"
    for article in vol2_articles:
        output_path = fetch_zenn_article(article['url'], vol2_dir)
        if output_path:
            # メタデータファイルも作成
            meta_path = output_path.replace('.md', '_meta.txt')
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write(f"Rank: {article['rank']}\n")
                f.write(f"Name: {article['name']}\n")
                f.write(f"Team: {article['team']}\n")
                f.write(f"URL: {article['url']}\n")
        
        # レート制限を避けるため少し待機
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
