import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env if present
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def run_sql(sql):
    """
    Executes raw SQL using a stored procedure in Supabase.
    Note: Requires a 'exec_sql' function to be defined in your Supabase DB:
    
    create or replace function exec_sql(sql_text text)
    returns void
    language plpgsql
    security definer
    as $$
    begin
      execute sql_text;
    end;
    $$;
    """
    try:
        supabase.rpc("exec_sql", {"sql_text": sql}).execute()
        return True
    except Exception as e:
        print(f"Error executing SQL: {e}")
        return False

def setup_articles_table():
    print("Creating 'articles' table...")
    sql = """
    CREATE TABLE IF NOT EXISTS articles (
        id uuid primary key default gen_random_uuid(),
        title text not null,
        source_name text not null,
        original_url text not null unique,
        cover_image_url text,
        ai_summary text,
        sentiment text check (sentiment in ('Bullish', 'Bearish', 'Neutral')),
        genre_tags text[],
        key_takeaways text[],
        entities_mentioned jsonb,
        published_date timestamptz,
        crawled_date timestamptz default now()
    );
    
    ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
    
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = 'articles' AND policyname = 'Public SELECT access'
        ) THEN
            CREATE POLICY "Public SELECT access" ON articles FOR SELECT USING (true);
        END IF;
    END
    $$;
    """
    if run_sql(sql):
        print("Successfully created 'articles' table and configured RLS/Policy.")
    else:
        print("Failed to set up 'articles' table.")

def setup_article_blocks_table():
    print("Creating 'article_blocks' table...")
    sql = """
    CREATE TABLE IF NOT EXISTS article_blocks (
        id uuid primary key default gen_random_uuid(),
        article_id uuid references articles(id) on delete cascade,
        position integer not null,
        type text not null check (type in ('heading1', 'heading2', 'paragraph', 'image', 'bullet', 'quote')),
        text_content text,
        image_url text
    );
    
    ALTER TABLE article_blocks ENABLE ROW LEVEL SECURITY;
    
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = 'article_blocks' AND policyname = 'Public SELECT access'
        ) THEN
            CREATE POLICY "Public SELECT access" ON article_blocks FOR SELECT USING (true);
        END IF;
    END
    $$;
    """
    if run_sql(sql):
        print("Successfully created 'article_blocks' table and configured RLS/Policy.")
    else:
        print("Failed to set up 'article_blocks' table.")

def setup_crawl_runs_table():
    print("Creating 'crawl_runs' table...")
    sql = """
    CREATE TABLE IF NOT EXISTS crawl_runs (
        id uuid primary key default gen_random_uuid(),
        run_timestamp timestamptz default now(),
        articles_found integer default 0,
        sources_succeeded text[],
        sources_failed text[],
        gemini_calls_used integer default 0,
        error_log text
    );
    
    ALTER TABLE crawl_runs ENABLE ROW LEVEL SECURITY;
    
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = 'crawl_runs' AND policyname = 'Public SELECT access'
        ) THEN
            CREATE POLICY "Public SELECT access" ON crawl_runs FOR SELECT USING (true);
        END IF;
    END
    $$;
    """
    if run_sql(sql):
        print("Successfully created 'crawl_runs' table and configured RLS/Policy.")
    else:
        print("Failed to set up 'crawl_runs' table.")

def run_setup():
    print("Starting database setup...")
    setup_articles_table()
    setup_article_blocks_table()
    setup_crawl_runs_table()
    print("\nDatabase setup process finished.")

if __name__ == "__main__":
    run_setup()
