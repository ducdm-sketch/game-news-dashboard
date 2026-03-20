import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_digest(articles: list) -> None:
    """
    Sends a digest of processed articles to a Discord webhook.
    Taking a list of article dicts with: title, source_name, original_url, ai_summary, sentiment, genre_tags.
    Respects Discord rate limits by sleeping between embed posts.
    """
    if not articles:
        return

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:3000").rstrip('/')

    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable is not set. Skipping Discord report.")
        return

    try:
        # 1. Send initial summary message
        print(f"Sending Discord summary for {len(articles)} articles...")
        summary_payload = {
            "content": f"📰 New articles found: {len(articles)}"
        }
        requests.post(webhook_url, json=summary_payload, timeout=15)
        
        # 2. Mapping for visual flair
        sentiment_map = {
            "Bullish": {"emoji": "🟢", "color": 3066993},  # Green
            "Bearish": {"emoji": "🔴", "color": 15158332}, # Red
            "Neutral": {"emoji": "⚪", "color": 10197915}  # Gray/Silver
        }

        # 3. Send one embed per article
        for article in articles:
            article_id = article.get("id", "unknown")
            title = article.get("title", "Untitled")
            source = article.get("source_name", "Unknown Source")
            url = article.get("original_url", "#")
            summary = article.get("ai_summary", "No summary provided.")
            sentiment = article.get("sentiment", "Neutral")
            tags = article.get("genre_tags", [])
            
            # Link title to the dashboard page
            article_link = f"{dashboard_url}/article/{article_id}"
            
            s_config = sentiment_map.get(sentiment, sentiment_map["Neutral"])
            
            embed = {
                "title": title,
                "url": article_link,
                "description": f"**Source:** {source} | {s_config['emoji']} **{sentiment}**",
                "color": s_config["color"],
                "fields": [
                    {
                        "name": "Summary",
                        "value": summary[:1020] + "..." if len(summary) > 1024 else summary
                    },
                    {
                        "name": "Tags",
                        "value": ", ".join(tags) if tags else "None",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Original: {url}"
                }
            }

            payload = {"embeds": [embed]}
            response = requests.post(webhook_url, json=payload, timeout=15)
            
            if response.status_code not in [200, 204]:
                print(f"Warning: Failed to send embed for '{title}'. Status code: {response.status_code}")

            # 4. Respect Discord rate limits (~5 requests per 2 seconds)
            time.sleep(2)

    except Exception as e:
        print(f"Error sending Discord digest: {e}")

def send_status_report(sources_succeeded: list, sources_failed: list, articles_found: int, gemini_calls: int, warnings: list) -> None:
    """
    Sends a final status report embed to Discord.
    Grades the run as OK, Warning, or Critical based on success rates and errors.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    try:
        # Respect rate limits from previous digest messages
        time.sleep(2)

        total_sources = len(sources_succeeded) + len(sources_failed)
        
        # 1. Determine Status Level
        # Default: OK
        status_emoji = "🟢"
        status_text = "OK"
        color = 3066993 # Green
        
        # Check for Critical
        is_supabase_error = any("supabase" in str(w).lower() for w in warnings)
        half_failed = len(sources_failed) > (total_sources / 2) if total_sources > 0 else False
        
        if is_supabase_error or half_failed:
            status_emoji = "🔴"
            status_text = "Critical"
            color = 15158332 # Red
        # Check for Warning
        elif sources_failed or warnings:
            status_emoji = "🟡"
            status_text = "Warning"
            color = 16776960 # Yellow

        # 2. Prepare Embed
        embed = {
            "title": f"{status_emoji} Crawl Run Complete - {status_text}",
            "color": color,
            "fields": [
                {"name": "Articles Found", "value": str(articles_found), "inline": True},
                {"name": "Gemini Calls", "value": str(gemini_calls), "inline": True},
                {"name": "Sources Succeeded", "value": str(len(sources_succeeded)), "inline": True},
            ],
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }

        if sources_failed:
            failed_names = ", ".join([str(s.get('name', 'Unknown')) if isinstance(s, dict) else str(s) for s in sources_failed])
            embed["fields"].append({"name": "Sources Failed", "value": failed_names, "inline": False})

        if warnings:
            warning_text = "\n".join([f"- {w}" for w in warnings])
            # Trim if too long for Discord field
            if len(warning_text) > 1020: warning_text = warning_text[:1020] + "..."
            embed["fields"].append({"name": "Warnings", "value": warning_text, "inline": False})

        payload = {"embeds": [embed]}
        requests.post(webhook_url, json=payload, timeout=15)
        print(f"Status report sent: {status_text}")

    except Exception as e:
        print(f"Error sending Discord status report: {e}")

if __name__ == "__main__":
    # Internal test block
    test_data = [
        {
            "id": "test-1234",
            "title": "The Rise of Hybrid-Casual Games in 2026",
            "source_name": "Naavik",
            "original_url": "https://naavik.co/test",
            "ai_summary": "A deep dive into how hybrid-casual mechanics are replacing traditional hyper-casual models for better LTV.",
            "sentiment": "Bullish",
            "genre_tags": ["Hybrid-Casual", "Market Data", "Game Design"]
        }
    ]
    
    print("Running Discord reporter verification...")
    # This will naturally fail to POST if no webhook is set, but tests the logic flow.
    send_digest(test_data)
