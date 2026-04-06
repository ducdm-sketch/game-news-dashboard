import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configuration
AI_CALL_COUNT_FILE = os.path.join(os.getcwd(), "tmp", "ai_call_count.txt")
MAX_AI_CALLS = 50
REQUIRED_FIELDS = {"summary", "key_takeaways", "entities", "genre_tags"}
VALID_GENRE_TAGS = {
    "Hyper-Casual", "Hybrid-Casual", "Casual", "Puzzle", "UA",
    "Monetization", "Market Data", "Game Design", "Industry News", "Business"
}

SYSTEM_PROMPT = """You are a senior analyst for a mobile game development studio. Your job is to extract factual information ONLY from the article provided. You must follow these strict rules:
- NEVER invent, infer, or assume any facts not explicitly stated in the article text
- If a field cannot be filled from the article text, use an empty array [] or the string 'Not specified'
- Do NOT pad key_takeaways with generic advice — only include insights directly supported by the article
- genre_tags must only use tags that genuinely apply to the article content"""

def _get_call_count() -> int:
    """Reads the current AI call count from the tmp file."""
    os.makedirs(os.path.dirname(AI_CALL_COUNT_FILE), exist_ok=True)
    try:
        with open(AI_CALL_COUNT_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def _increment_call_count():
    """Increments the AI call count in the tmp file."""
    count = _get_call_count() + 1
    with open(AI_CALL_COUNT_FILE, 'w') as f:
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
            .maybe_single() \
            .execute()
        data = response.data
        if data and data.get("ai_summary"):
            return True
    except Exception as e:
        print(f"Cache check failed (proceeding without cache): {e}")
    return False

def _parse_ai_response(raw_text: str) -> dict | None:
    """Strictly parses and validates the JSON response from the AI."""
    # Strip potential markdown code blocks
    text = raw_text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"AI JSON parse error: {e}\nRaw response: {raw_text[:300]}")
        return None

    # Check all required fields are present
    missing = REQUIRED_FIELDS - set(parsed.keys())
    if missing:
        print(f"AI response missing required fields: {missing}")
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
    Sends article content to Groq for analysis and returns structured insights.
    Returns None on cache hit, cap exceeded, parse error, or any failure.
    """
    try:
        # 1. Check Supabase cache
        if _check_supabase_cache(article_id):
            print(f"Cache hit for article {article_id}. Skipping AI call.")
            return None

        # 2. Check API call cap
        current_count = _get_call_count()
        if current_count >= MAX_AI_CALLS:
            print(f"Warning: AI API call cap ({MAX_AI_CALLS}) reached for this run. Skipping.")
            return None

        # 3. Configure OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY is not set. If running in GitHub Actions, ensure you have added it to Repository Secrets.")
            return None

        client = OpenAI(api_key=api_key)

        # 4. Build and send prompt
        # Truncate full_text to avoid token limit issues
        truncated_text = full_text[:12000] if len(full_text) > 12000 else full_text
        user_message = f"""Analyze the following article and return a JSON object with exactly these fields:

- summary: One sentence. Must include the WHO (company/game), WHAT (the key event or finding), and WHY it matters. Use only facts from the article.

- key_takeaways: Array of exactly 3 strings. Each must be a specific, actionable insight for a mobile game developer. Each must cite a specific fact, number, or example from the article. Never write generic advice.

- entities: Object with three arrays:
  - games: exact game titles mentioned in the article
  - studios: exact company or studio names mentioned
  - metrics: exact numeric data mentioned (e.g. 'D7 retention 34%', 'CPI $1.20', 'DAU 2.3M') — copy the numbers exactly as written

- genre_tags: Array using only these tags where genuinely applicable: Hyper-Casual, Hybrid-Casual, Casual, Puzzle, UA, Monetization, Market Data, Game Design, Industry News, Business

Article title: {title}
Article text:
{truncated_text}"""

        _increment_call_count()
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="GPT-5.4 nano",
            response_format={"type": "json_object"},
        )

        # 5. Parse and validate response
        raw_text = chat_completion.choices[0].message.content
        result = _parse_ai_response(raw_text)

        if result is None:
            return None

        return result

    except Exception as e:
        print(f"Error analyzing article '{title}': {e}")
        return None

if __name__ == "__main__":
    # Reset call count for test
    os.makedirs("tmp", exist_ok=True)
    with open(AI_CALL_COUNT_FILE, 'w') as f:
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

    print("Testing OpenAI analysis...")
    result = analyze_article("test-article-001", sample_title, sample_text)
    if result:
        print(f"Summary: {result['summary']}")
        print(f"Key Takeaways: {result['key_takeaways']}")
        print(f"Genre Tags: {result['genre_tags']}")
        print(f"Entities: {result['entities']}")
    else:
        print("Analysis returned None (check credentials or cache hit).")
