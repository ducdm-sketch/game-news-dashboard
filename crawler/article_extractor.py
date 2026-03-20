import os
import re
import requests
import uuid
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
# Using a local tmp directory relative to project root for cross-platform compatibility
TEMP_IMAGE_DIR = os.path.join(os.getcwd(), "tmp", "images")
MAX_IMAGES_PER_ARTICLE = 20

# Create temp dir if it doesn't exist
if not os.path.exists(TEMP_IMAGE_DIR):
    os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=4, min=4, max=60),
    reraise=True
)
def fetch_html(url, substack_cookie=None):
    """Fetches HTML with retries and optional cookies."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    cookies = {}
    if substack_cookie:
        # Simple cookie string parsing if provided as 'key=value; key2=value2'
        for pair in substack_cookie.split(';'):
            if '=' in pair:
                parts = pair.strip().split('=', 1)
                if len(parts) == 2:
                    cookies[parts[0]] = parts[1]
    
    response = requests.get(url, headers=headers, cookies=cookies, timeout=20)
    response.raise_for_status()
    return response.text

def download_image(url, folder):
    """Downloads an image and returns the local path."""
    try:
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Extract extension or default to .jpg
        parsed_path = urlparse(url).path
        ext = os.path.splitext(parsed_path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'
        
        filename = f"{uuid.uuid4().hex}{ext}"
        local_path = os.path.join(folder, filename)
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return local_path
    except Exception:
        return None

def extract_article(url: str, source_name: str, substack_cookie: str = None) -> dict:
    """
    Main extraction function for article content.
    Returns structured blocks and metadata.
    """
    try:
        html = fetch_html(url, substack_cookie)
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Extract Title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Untitled Article"
        
        # 2. Find Cover Image (og:image)
        cover_image_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            cover_image_url = og_image['content']
            
        # 3. Noise Removal
        # Remove standard noise blocks
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            tag.decompose()
            
        # Remove elements with noise-related class names
        noise_keywords = ["ad", "advertisement", "sidebar", "related", "newsletter", "subscribe", "comment"]
        for tag in soup.find_all(class_=True):
            if tag.name in ['body', 'html', 'main']:
                continue
            if not getattr(tag, 'attrs', None):
                continue
            classes = tag.get('class', [])
            if not isinstance(classes, list):
                classes = [classes]
                
            is_noise = False
            for cls in classes:
                cls_lower = cls.lower()
                # Exact matches or prefix/suffix for 'ad' to avoid matching 'kadence' or 'thread'
                if cls_lower in ['ad', 'ads', 'advert'] or cls_lower.startswith('ad-') or cls_lower.endswith('-ad') or cls_lower.startswith('advertisement'):
                    is_noise = True
                    break
                # Other keywords can be substrings
                if any(kw in cls_lower for kw in ["sidebar", "related", "newsletter", "subscribe", "comment"]):
                    is_noise = True
                    break
            
            if is_noise:
                tag.decompose()

        # 4. Content Block Extraction
        blocks = []
        local_images = []
        image_count = 0
        
        # Target the main content area if possible
        content_container = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|post|article', re.I)) or soup.body
        
        if not content_container:
            return None

        # Iterate through relevant tags in order to preserve structure
        for tag in content_container.find_all(['h1', 'h2', 'h3', 'p', 'li', 'blockquote', 'img']):
            block = None
            
            if tag.name == 'h1':
                block = {"type": "heading1", "content": tag.get_text(strip=True)}
            elif tag.name in ['h2', 'h3']:
                block = {"type": "heading2", "content": tag.get_text(strip=True)}
            elif tag.name == 'p':
                text = tag.get_text(strip=True)
                if len(text) >= 30:
                    block = {"type": "paragraph", "content": text}
            elif tag.name == 'li':
                # Only include if inside a list
                if tag.parent and tag.parent.name in ['ul', 'ol']:
                    block = {"type": "bullet", "content": tag.get_text(strip=True)}
            elif tag.name == 'blockquote':
                block = {"type": "quote", "content": tag.get_text(strip=True)}
            elif tag.name == 'img' and image_count < MAX_IMAGES_PER_ARTICLE:
                # Handle lazy loading scenarios
                src = tag.get('src') or tag.get('data-src') or tag.get('srcset')
                if src:
                    # Clean up srcset if needed
                    if ',' in src: src = src.split(',')[0].split(' ')[0]
                    img_url = urljoin(url, src)
                    alt = tag.get('alt', '')
                    local_path = download_image(img_url, TEMP_IMAGE_DIR)
                    if local_path:
                        local_images.append(local_path)
                        image_count += 1
                        block = {"type": "image", "content": {"src": img_url, "alt": alt, "local_path": local_path}}

            if block and block.get("content"):
                blocks.append(block)

        # 5. Download cover image if found
        cover_image_path = None
        if cover_image_url:
            cover_image_path = download_image(cover_image_url, TEMP_IMAGE_DIR)
            if cover_image_path:
                local_images.append(cover_image_path)

        return {
            "title": title,
            "cover_image_path": cover_image_path,
            "blocks": blocks,
            "local_image_paths": local_images
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error extracting article from {url}: {e}")
        return None

if __name__ == "__main__":
    # Internal test with a public article
    sample_url = "https://naavik.co/deep-dives/gdc-2026-recap/"
    print(f"Testing extraction on: {sample_url}")
    result = extract_article(sample_url, "Naavik")
    if result:
        print(f"Title: {result['title']}")
        print(f"Blocks: {len(result['blocks'])}")
        print(f"Images: {len(result['local_image_paths'])}")
        for i, b in enumerate(result['blocks'][:5]):
            print(f"Block {i} [{b['type']}]: {str(b['content'])[:50]}...")
