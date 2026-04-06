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
REQUIRED_FIELDS = {"summary", "key_takeaways", "genre_tags", "entities", "is_pure_news", "viet_summary", "viet_action_items"}
VALID_GENRE_TAGS = {
    "Hyper-Casual", "Hybrid-Casual", "Casual", "Puzzle", "UA",
    "Monetization", "Market Data", "Game Design", "Industry News", "Business"
}

SYSTEM_PROMPT = """
You are a senior mobile game industry analyst working internally for Pixon Game Studio — a mobile game developer and publisher based in Hanoi, Vietnam, under FPT Corporation. Pixon focuses on Hyper-casual, Hybrid-casual, Casual, and Puzzle mobile games, and both self-develops and publishes for indie teams.

Internal teams reading this analysis:
- Game Research: genre trends, new mechanics, top charts, emerging games
- UA: CPI benchmarks, creative formats, platform policy, SKAdNetwork/ATT, ROAS
- Monetization: ad revenue, IAP meta, rewarded video, mediation, eCPM, LiveOps
- Game Design: retention mechanics, core loops, progression systems, first-hour UX

Competitors to flag: Voodoo, Kwalee, SayGames, Miniclip, Zeptolab, Amanotes.
Key markets: Global (priority: US, EU) and Southeast Asia (especially Vietnam).

YOUR TASK:
Analyze the article provided and return a single JSON object with two sections:

SECTION 1 — ENGLISH (stored in database):
These fields must be in English only. Keep all industry terms in English: retention, revenue, CPI, ROAS, eCPM, DAU, MAU, LTV, IAP, D7/D30, churn, mediation, LiveOps, playable ads, soft launch, meta-game, etc.

SECTION 2 — VIETNAMESE DISPLAY (sent to Discord):
A human-readable narrative in Vietnamese for the team's daily digest. Keep all industry jargon, metrics, game names, studio names, and platform names in English within the Vietnamese text. Do NOT translate: retention, revenue, CPI, ROAS, eCPM, DAU, LTV, IAP, D7, D30, LiveOps, meta-game, soft launch, top chart, benchmark, mediation, rewarded video, playable ads, core loop, hyper-casual, hybrid-casual.

IMPORTANT RULES:
- Never invent facts, numbers, or names not explicitly stated in the article.
- If the article is pure news reporting (a launch announcement, acquisition, earnings report with no analysis), set "is_pure_news": true — in this case, "key_takeaways" should be [] and "viet_action_items" should be [] (no recommendations for pure news).
- If the article contains analysis, benchmarks, case studies, or actionable data, set "is_pure_news": false and populate all fields fully.
- Each key_takeaway and viet_action_item must cite a specific number, game name, or quote from the article.

RETURN THIS EXACT JSON SCHEMA:
{
  "summary": "<one sentence in English: WHO did WHAT and WHY it matters>",
  "key_takeaways": ["<specific English insight with cited fact>", "<...>", "<...>"],
  "genre_tags": ["<only from: Hyper-Casual, Hybrid-Casual, Casual, Puzzle, UA, Monetization, Market Data, Game Design, Industry News, Business>"],
  "entities": {
    "games": ["<exact game titles mentioned>"],
    "studios": ["<exact studio/company names mentioned>"],
    "metrics": ["<exact numeric data as written, e.g. 'D7 retention 34%', 'CPI $1.20'>"]
  },
  "is_pure_news": true | false,
  "viet_summary": "<1-2 câu tóm tắt bằng tiếng Việt, giữ nguyên jargon tiếng Anh>",
  "viet_action_items": [
    {
      "viec_can_lam": "<hành động cụ thể>",
      "ly_do": "<dẫn chứng số liệu hoặc ví dụ từ bài viết>",
      "nhom": "UA | Monetization | Game Design | Game Research",
      "uu_tien": "cao | trung_binh | thap"
    }
  ]
}
"""

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

    # Validate key_takeaways length (0-5 items)
    if not isinstance(parsed.get("key_takeaways"), list) or not (0 <= len(parsed["key_takeaways"]) <= 5):
        print(f"key_takeaways must be a list of 0-5 items.")
        return None

    # Check is_pure_news constraint: if True, action items MUST be empty
    if parsed.get("is_pure_news") is True and parsed.get("viet_action_items"):
        print(f"Warning: is_pure_news is True but viet_action_items is not empty. Clearing it.")
        parsed["viet_action_items"] = []

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
        user_message = f"""Article title: {title}
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
            model="gpt-5.4-nano",
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

    print("Testing OpenAI analysis (Pixon Analyst)...")
    result = analyze_article("test-article-001", sample_title, sample_text)
    if result:
        print(f"Summary (EN): {result.get('summary')}")
        print(f"Summary (VN): {result.get('viet_summary')}")
        print(f"Is Pure News: {result.get('is_pure_news')}")
        print(f"Action Items: {len(result.get('viet_action_items', []))}")
        print(f"Genre Tags: {result.get('genre_tags')}")
    else:
        print("Analysis returned None (check credentials or cache hit).")
