-- Supabase Schema Initialization Script
-- Run this in the Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql)

-- 1. Create 'articles' table
CREATE TABLE IF NOT EXISTS articles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL,
    source_name text NOT NULL,
    original_url text NOT NULL UNIQUE,
    cover_image_url text,
    ai_summary text,
    genre_tags text[],
    key_takeaways text[],
    entities_mentioned jsonb,
    published_date timestamptz,
    crawled_date timestamptz DEFAULT now()
);

-- 2. Create 'article_blocks' table
CREATE TABLE IF NOT EXISTS article_blocks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id uuid REFERENCES articles(id) ON DELETE CASCADE,
    position integer NOT NULL,
    type text NOT NULL CHECK (type IN ('heading1', 'heading2', 'paragraph', 'image', 'bullet', 'quote')),
    text_content text,
    image_url text
);

-- 3. Create 'crawl_runs' table
CREATE TABLE IF NOT EXISTS crawl_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_timestamp timestamptz DEFAULT now(),
    articles_found integer DEFAULT 0,
    sources_succeeded text[],
    sources_failed text[],
    gemini_calls_used integer DEFAULT 0,
    error_log text
);

-- 4. Enable Row Level Security (RLS) on all tables
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawl_runs ENABLE ROW LEVEL SECURITY;

-- 5. Create Policies for unrestricted public read (SELECT) access
CREATE POLICY "Public SELECT access" ON articles FOR SELECT USING (true);
CREATE POLICY "Public SELECT access" ON article_blocks FOR SELECT USING (true);
CREATE POLICY "Public SELECT access" ON crawl_runs FOR SELECT USING (true);
