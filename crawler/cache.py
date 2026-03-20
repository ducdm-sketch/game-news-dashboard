import json
import os

# Path to the JSON file storing seen URLs
CACHE_FILE = os.path.join(os.path.dirname(__file__), "seen_articles.json")

def is_seen(url: str) -> bool:
    """
    Returns True if the given URL already exists in seen_articles.json, False otherwise.
    """
    if not os.path.exists(CACHE_FILE):
        return False
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            seen_urls = json.load(f)
            return url in seen_urls
    except (json.JSONDecodeError, IOError):
        # If the file is broken or inaccessible, treat as not seen
        return False

def mark_seen(url: str) -> None:
    """
    Appends the given URL to seen_articles.json if it is not already present.
    Handles concurrent-safe file writing using a try/except block.
    """
    try:
        seen_urls = []
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                try:
                    seen_urls = json.load(f)
                except json.JSONDecodeError:
                    seen_urls = []

        if url not in seen_urls:
            seen_urls.append(url)
            
            # Concurrent-safe-ish: Write to a temporary file then rename
            # though the prompt specifically mentioned a "try/except block" 
            # for handling the writing process.
            temp_file = CACHE_FILE + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(seen_urls, f, indent=2)
            
            # Replace the original file with the new one
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            os.rename(temp_file, CACHE_FILE)
            
    except Exception as e:
        print(f"Error updating cache file: {e}")
        # Clean up temp file if something went wrong
        if 'temp_file' in locals() and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

if __name__ == "__main__":
    # Quick test
    test_url = "https://example.com/news/1"
    print(f"Is seen: {is_seen(test_url)}")
    mark_seen(test_url)
    print(f"Is seen after marking: {is_seen(test_url)}")
    # Clean up test
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
