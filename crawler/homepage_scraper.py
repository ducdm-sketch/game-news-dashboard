import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from crawler.cache import is_seen

def scrape_new_articles(sources: list) -> list:
    """
    Scrapes new article links from the provided list of website sources.
    Uses CSS selectors from the source config to find links.
    """
    all_new_articles = []
    
    # Realistic browser User-Agent to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    for source in sources:
        try:
            name = source.get('name')
            url = source.get('url')
            selector = source.get('css_selector')
            tags = source.get('tags', [])

            if not selector:
                print(f"Warning: No css_selector defined for source '{name}'. Skipping.")
                continue

            print(f"Scraping homepage: {name} ({url})...")
            
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all elements matching the CSS selector
            elements = soup.select(selector)
            
            for el in elements:
                # Expecting the selector to target <a> tags or elements containing them
                link_tag = el if el.name == 'a' else el.find('a')
                
                if not link_tag or not link_tag.get('href'):
                    continue
                
                article_url = urljoin(url, link_tag['href'])
                article_title = link_tag.get_text(strip=True) or el.get_text(strip=True)
                
                # Basic cleaning of title
                if not article_title:
                    continue

                # Filter out already seen URLs
                if is_seen(article_url):
                    continue
                
                all_new_articles.append({
                    "title": article_title,
                    "url": article_url,
                    "source_name": name,
                    "source_tags": tags
                })

        except Exception as e:
            print(f"Error scraping source '{source.get('name', 'Unknown')}': {e}")
            continue

    return all_new_articles

if __name__ == "__main__":
    # Internal test: Attempt to scrape a public news site if a scrape source was provided
    # Since sources.json only has RSS for now, we'll use a dummy test case
    test_sources = [
        {
            "name": "Hacker News",
            "url": "https://news.ycombinator.com/",
            "type": "scrape",
            "css_selector": ".titleline > a",
            "tags": ["Tech"]
        }
    ]
    print("Testing scraper with Hacker News...")
    articles = scrape_new_articles(test_sources)
    print(f"Found {len(articles)} new articles on HN.")
    if articles:
        print(f"Example: {articles[0]['title']} -> {articles[0]['url']}")
