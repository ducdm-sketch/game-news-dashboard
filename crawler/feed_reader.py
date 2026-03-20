import feedparser
import requests
import os
import json
from datetime import datetime, timedelta, timezone
from crawler.cache import is_seen
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_new_articles(sources: list) -> list:
    """
    Accepts a list of source objects, fetches their RSS/Substack feeds, 
    and returns a list of new articles from the last 7 days.
    """
    all_new_articles = []
    # 7-day cutoff (timezone-aware UTC)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    substack_cookie = os.getenv("SUBSTACK_COOKIE")

    for source in sources:
        try:
            name = source.get('name')
            url = source.get('url')
            source_type = source.get('type')
            tags = source.get('tags', [])

            # Only process RSS and Substack
            if source_type not in ['rss', 'substack']:
                continue

            print(f"Reading feed: {name}...")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-CH-UA': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"Windows"',
            }
            if source_type == 'substack' and substack_cookie:
                headers['Cookie'] = substack_cookie

            # Fetch the feed content
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            # Parse the feed
            feed = feedparser.parse(response.text)

            for entry in feed.entries:
                link = entry.get('link')
                title = entry.get('title')
                
                # 1. Skip if already seen
                if is_seen(link):
                    continue

                # 2. Parse and filter by date
                # feedparser provides published_parsed as a time.struct_time
                published_parsed = entry.get('published_parsed')
                if published_parsed:
                    # Convert to timezone-aware datetime (UTC)
                    pub_date = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                else:
                    # Fallback to current time if no date is available
                    pub_date = datetime.now(timezone.utc)

                if pub_date < seven_days_ago:
                    continue

                # 3. Add to the list
                all_new_articles.append({
                    "title": title,
                    "url": link,
                    "source_name": name,
                    "source_tags": tags,
                    "published_date": pub_date.isoformat()
                })

        except Exception as e:
            print(f"Error processing source '{source.get('name', 'Unknown')}': {e}")
            continue

    return all_new_articles

if __name__ == "__main__":
    # Internal test: load sources.json and fetch from the first one
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config", "sources.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                sources = json.load(f)
                # Test with the first valid RSS/Substack source
                test_sources = [s for s in sources if s['type'] in ['rss', 'substack']]
                if test_sources:
                    print(f"Attempting to fetch from: {test_sources[0]['name']}")
                    articles = fetch_new_articles(test_sources[:1])
                    print(f"Success! Found {len(articles)} new articles.")
                    if articles:
                        print(f"First article: {articles[0]['title']}")
    except Exception as e:
        print(f"Test failed: {e}")
