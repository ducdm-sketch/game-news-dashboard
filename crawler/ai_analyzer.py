import os
import json
import re
from google import genai
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configuration
GEMINI_CALL_COUNT_FILE = os.path.join(os.getcwd(), "tmp", "gemini_call_count.txt")
MAX_GEMINI_CALLS = 50
REQUIRED_FIELDS = {"summary", "key_takeaways", "entities", "sentiment", "genre_tags"}
VALID_SENTIMENTS = {"Bullish", "Bearish", "Neutral"}
VALID_GENRE_TAGS = {
    "Hyper-Casual", "Hybrid-Casual", "Casual", "Puzzle", "UA",
    "Monetization", "Market Data", "Game Design", "Industry News", "Business"
}

GEMINI_PROMPT_TEMPLATE = """You are an analyst for a mobile game development team focused on casual, hyper-casual, hybrid-casual, and puzzle games. Analyze the following article and return a JSON object with exactly these fields:
- summary: one sentence summarizing the article
- key_takeaways: an array of exactly 3 strings, each being a key insight for a mobile game developer
- entities: an object with three arrays: games (game titles mentioned), studios (company names mentioned), metrics (any numeric metrics mentioned e.g. D7 retention 22%, CPI $1.40)
- sentiment: exactly one of Bullish, Bearish, or Neutral — representing the overall outlook on the mobile gaming genre or topic covered
- genre_tags: an array of relevant tags from this list only: Hyper-Casual, Hybrid-Casual, Casual, Puzzle, UA, Monetization, Market Data, Game Design, Industry News, Business

Return ONLY valid JSON, no markdown code blocks, no preamble.

Article Title: {title}

Article Text:
{full_text}"""

def _get_call_count() -> int:
    """Reads the current Gemini call count from the tmp file."""
    os.makedirs(os.path.dirname(GEMINI_CALL_COUNT_FILE), exist_ok=True)
    try:
        with open(GEMINI_CALL_COUNT_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def _increment_call_count():
    """Increments the Gemini call count in the tmp file."""
    count = _get_call_count() + 1
    with open(GEMINI_CALL_COUNT_FILE, 'w') as f:
        f.write(str(count))
    return count

def _check_supabase_cache(article_id: str) -> bool:
    """Returns True if this article already has a non-null ai_summary in the DB."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return False
    try:
        supabase: Client = create_client(url, key)
        response = supabase.table("articles") \
            .select("ai_summary") \
            .eq("id", article_id) \
            .single() \
            .execute()
        data = response.data
        if data and data.get("ai_summary"):
            return True
    except Exception as e:
        print(f"Cache check failed (proceeding without cache): {e}")
    return False

def _parse_gemini_response(raw_text: str) -> dict | None:
    """Strictly parses and validates the JSON response from Gemini."""
    # Strip potential markdown code blocks
    text = raw_text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Gemini JSON parse error: {e}\nRaw response: {raw_text[:300]}")
        return None

    # Check all required fields are present
    missing = REQUIRED_FIELDS - set(parsed.keys())
    if missing:
        print(f"Gemini response missing required fields: {missing}")
        return None

    # Validate sentiment
    if parsed.get("sentiment") not in VALID_SENTIMENTS:
        print(f"Invalid sentiment value: {parsed.get('sentiment')}")
        return None

    # Validate key_takeaways has exactly 3 items
    if not isinstance(parsed.get("key_takeaways"), list) or len(parsed["key_takeaways"]) != 3:
        print(f"key_takeaways must be a list of exactly 3 items.")
        return None

    # Filter genre_tags to only valid values
    parsed["genre_tags"] = [t for t in parsed.get("genre_tags", []) if t in VALID_GENRE_TAGS]

    return parsed

def analyze_article(article_id: str, title: str, full_text: str, image_paths: list = None) -> dict:
    """
    Sends article content to Gemini for analysis and returns structured insights.
    Returns None on cache hit, cap exceeded, parse error, or any failure.
    """
    try:
        # 1. Check Supabase cache
        if _check_supabase_cache(article_id):
            print(f"Cache hit for article {article_id}. Skipping Gemini call.")
            return None

        # 2. Check API call cap
        current_count = _get_call_count()
        if current_count >= MAX_GEMINI_CALLS:
            print(f"Warning: Gemini API call cap ({MAX_GEMINI_CALLS}) reached for this run. Skipping.")
            return None

        # 3. Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable is not set.")
            return None

        client = genai.Client(api_key=api_key)

        # 4. Build and send prompt
        # Truncate full_text to avoid token limit issues (~12k chars ≈ ~3k tokens)
        truncated_text = full_text[:12000] if len(full_text) > 12000 else full_text
        prompt = GEMINI_PROMPT_TEMPLATE.format(title=title, full_text=truncated_text)

        _increment_call_count()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # 5. Parse and validate response
        raw_text = response.text
        result = _parse_gemini_response(raw_text)

        if result is None:
            return None

        return result

    except Exception as e:
        print(f"Error analyzing article '{title}': {e}")
        return None

if __name__ == "__main__":
    # Reset call count for test
    os.makedirs("tmp", exist_ok=True)
    with open(GEMINI_CALL_COUNT_FILE, 'w') as f:
        f.write("0")

    sample_title = "Why Hybrid-Casual Is the Future of Mobile Gaming"
    sample_text = """
    The mobile gaming market has been shifting dramatically over the past two years. 
    Hyper-casual games, once the dominant genre with CPIs as low as $0.15, are now 
    struggling against rising UA costs averaging $1.20. Studios like Voodoo and Kwalee 
    have pivoted hard towards hybrid-casual titles that combine simple core loops with 
    deeper meta-games, IAP, and battle passes. Key metrics show D7 retention improving 
    from 15% to 22% in these new hybrid titles. Games like Royal Match and Mob Control 
    demonstrate that the sweet spot is accessible gameplay married to aspirational progression.
    """

    print("Testing Gemini analysis...")
    result = analyze_article("test-article-001", sample_title, sample_text)
    if result:
        print(f"\nSentiment: {result['sentiment']}")
        print(f"Summary: {result['summary']}")
        print(f"Key Takeaways: {result['key_takeaways']}")
        print(f"Genre Tags: {result['genre_tags']}")
        print(f"Entities: {result['entities']}")
    else:
        print("Analysis returned None (check credentials or cache hit).")
