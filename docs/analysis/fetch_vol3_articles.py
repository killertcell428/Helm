"""
vol3の受賞記事を取得するスクリプト
vol3の受賞情報が確認でき次第、URLを追加して実行
"""
import requests
from bs4 import BeautifulSoup
import markdownify
import os
import time
from pathlib import Path

# スクリプトのディレクトリを取得
SCRIPT_DIR = Path(__file__).parent.absolute()

def fetch_zenn_article(url, output_dir="award_articles"):
    """
    Zenn記事を取得してMarkdown形式に変換
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
            article = soup.find('main') or soup.find('div', class_='article')
        
        if article:
            md_content = markdownify.markdownify(
                str(article),
                heading_style="ATX",
                bullets="-"
            )
            
            full_content = f"""# {title}

**URL**: {url}
**取得日**: {time.strftime('%Y-%m-%d %H:%M:%S')}

---

{md_content}
"""
            
            filename = url.split('/')[-1] + '.md'
            filename = filename.replace('?', '_').replace('&', '_')
            
            # 出力ディレクトリを絶対パスに変換
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(SCRIPT_DIR, output_dir)
            
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            print(f"[OK] Saved: {output_path}")
            return output_path
        else:
            print(f"[ERROR] Article content not found: {url}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Error fetching {url}: {str(e)}")
        return None

def main():
    """メイン処理"""
    
    # vol3の受賞記事URL
    vol3_articles = [
        {
            'url': 'https://zenn.dev/666giru/articles/04fef6731d041c',
            'rank': '要確認',
            'name': 'MindEcho',
            'team': 'MindEcho'
        },
        {
            'url': 'https://zenn.dev/yuma_s81128/articles/751220cc0fee2c',
            'rank': '要確認',
            'name': 'Coco-Ai (ココアイ)',
            'team': '個人'
        },
        {
            'url': 'https://zenn.dev/hosazaemoooon/articles/6f55eb1e53bd74',
            'rank': '要確認',
            'name': 'らんらんるんるん',
            'team': '個人'
        },
        {
            'url': 'https://zenn.dev/tenyyprn/articles/9965fd0b8f144a',
            'rank': '要確認',
            'name': 'Smart Chore App',
            'team': '個人'
        },
    ]
    
    if not vol3_articles:
        print("=" * 60)
        print("vol3の受賞記事URLが設定されていません。")
        print("vol3のプロジェクト一覧ページから受賞記事のURLを抽出して、")
        print("このスクリプトのvol3_articlesリストに追加してください。")
        print("=" * 60)
        return
    
    print("=" * 60)
    print("Fetching vol3 articles...")
    print("=" * 60)
    
    vol3_dir = "award_articles/vol3"
    for article in vol3_articles:
        output_path = fetch_zenn_article(article['url'], vol3_dir)
        if output_path:
            meta_path = output_path.replace('.md', '_meta.txt')
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write(f"Rank: {article['rank']}\n")
                f.write(f"Name: {article['name']}\n")
                f.write(f"Team: {article['team']}\n")
                f.write(f"URL: {article['url']}\n")
        
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
