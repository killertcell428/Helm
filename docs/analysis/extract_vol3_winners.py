"""
vol3のプロジェクト一覧ページから受賞記事のURLを抽出するスクリプト
"""
import requests
from bs4 import BeautifulSoup
import re

def extract_vol3_winners():
    """vol3のプロジェクト一覧ページから受賞記事のURLを抽出"""
    url = "https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol3?tab=projects"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 受賞情報を探す（「最優秀賞」「2位」「3位」などのキーワード）
        # Zennのプロジェクト一覧ページの構造に応じて調整が必要
        
        # 記事リンクを探す
        article_links = []
        
        # 一般的なパターン: <a>タグで記事へのリンクを探す
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/articles/' in href:
                full_url = f"https://zenn.dev{href}" if href.startswith('/') else href
                title = link.get_text().strip()
                
                # 受賞関連のキーワードを探す
                parent_text = ""
                if link.parent:
                    parent_text = link.parent.get_text()
                
                # 受賞情報が含まれているかチェック
                award_keywords = ['最優秀賞', '2位', '3位', 'Tech Deep Dive', 'Moonshot', 'Firebase', '受賞']
                if any(keyword in parent_text or keyword in title for keyword in award_keywords):
                    article_links.append({
                        'url': full_url,
                        'title': title,
                        'context': parent_text[:200]  # 前後の文脈
                    })
        
        print(f"\nFound {len(article_links)} potential award articles:")
        for i, article in enumerate(article_links, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")
            print(f"   Context: {article['context']}")
        
        return article_links
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

if __name__ == "__main__":
    print("=" * 60)
    print("Extracting vol3 winner article URLs...")
    print("=" * 60)
    articles = extract_vol3_winners()
    
    if articles:
        print("\n" + "=" * 60)
        print("Extraction complete!")
        print("=" * 60)
        print("\nPlease review the URLs above and add them to fetch_vol3_articles.py")
    else:
        print("\n" + "=" * 60)
        print("No articles found. The page structure may have changed.")
        print("Please manually check: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol3?tab=projects")
        print("=" * 60)
