import os
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Import crawler modules
from crawler.preflight import run_preflight
from crawler.feed_reader import fetch_new_articles
from crawler.homepage_scraper import scrape_new_articles
from crawler.article_extractor import extract_article
from crawler.image_uploader import upload_images
from crawler.ai_analyzer import analyze_article, _get_call_count
from crawler.cache import mark_seen
from crawler.discord_reporter import send_digest, send_status_report

# Load environment variables
load_dotenv()

MAX_ARTICLES_PER_RUN = 50

def run_crawler():
    """Main crawler orchestration loop."""
    run_timestamp = datetime.utcnow().isoformat()
    warnings = []
    
    try:
        # 1. PREFLIGHT
        print("--- Starting Preflight Checks ---")
        valid_sources, preflight_warnings = run_preflight()
        warnings.extend(preflight_warnings)
        
        if not valid_sources:
            print("Critical: No valid sources available.")
            send_status_report([], ["All sources failed validation"], 0, 0, warnings)
            return

        # 2. DISCOVERY
        print("\n--- Starting Discovery ---")
        rss_sources = [s for s in valid_sources if s['type'] in ('rss', 'substack')]
        scrape_sources = [s for s in valid_sources if s['type'] == 'scrape']
        
        new_articles = []
        if rss_sources:
            new_articles.extend(fetch_new_articles(rss_sources))
        if scrape_sources:
            new_articles.extend(scrape_new_articles(scrape_sources))
        
        if not new_articles:
            print("No new articles found.")
            send_status_report(valid_sources, [], 0, 0, warnings)
            return
            
        print(f"Discovered {len(new_articles)} potential new articles.")
        
        # Determine source tracking
        source_names = {s['name'] for s in valid_sources}
        sources_succeeded = set()
        sources_failed = set()

        # 3. PROCESS EACH ARTICLE
        print("\n--- Starting Processing ---")
        successfully_processed = []
        
        # Init Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        substack_cookie = os.getenv("SUBSTACK_COOKIE")

        for i, article in enumerate(new_articles[:MAX_ARTICLES_PER_RUN]):
            title = article['title']
            url = article['url']
            source_name = article['source_name']
            
            print(f"\n[{i+1}/{min(len(new_articles), MAX_ARTICLES_PER_RUN)}] Processing: {title}")
            
            try:
                # a. Extract Article
                extracted = extract_article(url, source_name, substack_cookie)
                if not extracted:
                    print(f"Skipping {url}: Extraction failed.")
                    sources_failed.add(source_name)
                    continue
                
                # b. Generate UUID
                article_id = str(uuid.uuid4())
                
                # c. Upload Images
                url_mapping = upload_images(article_id, extracted.get('local_image_paths', []))
                
                # d. Update Image Blocks
                blocks = extracted.get('blocks', [])
                full_text_parts = []
                
                for block in blocks:
                    if block['type'] == 'image' and 'content' in block:
                        local_path = block['content'].get('local_path')
                        if local_path and local_path in url_mapping:
                            block['content']['r2_url'] = url_mapping[local_path]
                    elif block['type'] in ('paragraph', 'heading1', 'heading2', 'bullet', 'quote'):
                        full_text_parts.append(block['content'])
                
                # e. Update Cover Image
                cover_image_path = extracted.get('cover_image_path')
                r2_cover_url = None
                if cover_image_path and cover_image_path in url_mapping:
                    r2_cover_url = url_mapping[cover_image_path]
                
                # f. AI Analysis
                full_text = "\\n".join(full_text_parts)
                ai_data = analyze_article(article_id, title, full_text)
                
                # Prepare DB Record
                db_article = {
                    "id": article_id,
                    "title": title,
                    "source_name": source_name,
                    "original_url": url,
                    "cover_image_url": r2_cover_url,
                    "published_date": article.get('published_date'),
                    "crawled_date": datetime.utcnow().isoformat()
                }
                
                if ai_data:
                    db_article["ai_summary"] = ai_data.get("summary")
                    db_article["sentiment"] = ai_data.get("sentiment")
                    db_article["genre_tags"] = ai_data.get("genre_tags", [])
                    db_article["key_takeaways"] = ai_data.get("key_takeaways", [])
                    db_article["entities_mentioned"] = ai_data.get("entities", {})
                
                # g. Save Article to Supabase
                supabase.table("articles").insert(db_article).execute()
                
                # h. Save Blocks to Supabase
                db_blocks = []
                for pos, block in enumerate(blocks):
                    db_block = {
                        "article_id": article_id,
                        "position": pos,
                        "type": block['type'],
                        "text_content": block.get('content') if isinstance(block.get('content'), str) else None,
                        "image_url": block['content'].get('r2_url') if isinstance(block['content'], dict) else None
                    }
                    db_blocks.append(db_block)
                
                if db_blocks:
                    supabase.table("article_blocks").insert(db_blocks).execute()
                
                # i. Mark Seen
                mark_seen(url)
                
                # j. Success
                successfully_processed.append(db_article)
                sources_succeeded.add(source_name)
                print(f"Successfully processed: {title}")

            except Exception as e:
                print(f"Error processing article {url}: {e}")
                sources_failed.add(source_name)
                warnings.append(f"Processing error for {source_name}: {str(e)[:100]}")

        # Finalize success/failure tracking
        for s in source_names:
            if s not in sources_succeeded and s not in sources_failed:
                # If a source had no new articles, it technically succeeded tracking
                sources_succeeded.add(s)

        # 4. DISCORD DIGEST
        print(f"\n--- Sending Digest ({len(successfully_processed)} articles) ---")
        send_digest(successfully_processed)

        # 5. CRAWL RUN LOG
        try:
            gemini_calls = _get_call_count()
        except:
            gemini_calls = 0
            
        run_log = {
            "run_timestamp": run_timestamp,
            "articles_found": len(successfully_processed),
            "sources_succeeded": list(sources_succeeded),
            "sources_failed": list(sources_failed),
            "gemini_calls_used": gemini_calls,
            "error_log": warnings
        }
        
        try:
            supabase.table("crawl_runs").insert(run_log).execute()
        except Exception as e:
            print(f"Failed to log run to DB: {e}")
            warnings.append(f"Supabase Run Log Error: {str(e)[:100]}")

        # 6. DISCORD STATUS
        print("\n--- Sending Status Report ---")
        send_status_report(
            sources_succeeded=list(sources_succeeded),
            sources_failed=list(sources_failed),
            articles_found=len(successfully_processed),
            gemini_calls=gemini_calls,
            warnings=warnings
        )
        
        print("\nCrawl Run Complete.")

    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"CRITICAL SYSTEM FAILURE:\n{err_msg}")
        warnings.append("CRITICAL UNHANDLED EXCEPTION in main crawler loop.")
        try:
            send_status_report([], ["SYSTEM FAILURE"], 0, 0, [err_msg[:1000]])
        except:
            pass

if __name__ == "__main__":
    run_crawler()
