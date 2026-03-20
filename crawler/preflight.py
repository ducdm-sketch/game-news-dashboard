import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from jsonschema import validate, ValidationError
from crawler.config_validator import SOURCE_SCHEMA

# Load environment variables
load_dotenv()

def run_preflight():
    """
    Runs pre-crawl checks: source validation, DB connectivity, and env checks.
    Returns: (valid_sources, warnings)
    """
    valid_sources = []
    warnings = []
    
    # 1. Validate sources from config/sources.json
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config", "sources.json")
    
    if not os.path.exists(config_path):
        warnings.append(f"Configuration file missing: {config_path}")
        return [], warnings

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            all_sources = json.load(f)
    except Exception as e:
        warnings.append(f"Failed to parse sources.json: {e}")
        return [], warnings

    for idx, source in enumerate(all_sources):
        try:
            validate(instance=source, schema=SOURCE_SCHEMA)
            valid_sources.append(source)
        except ValidationError as e:
            source_name = source.get('name', f"Source at index {idx}")
            warnings.append(f"Invalid config for '{source_name}': {e.message}")

    # 2. Ping Supabase (SELECT 1)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        warnings.append("Supabase environment variables (URL/KEY) are missing.")
    else:
        try:
            supabase: Client = create_client(url, key)
            # Using RPC to run raw SQL (SELECT 1) as requested. 
            # Note: This assumes 'exec_sql' exists or uses a standard postgrest health check approach.
            # For a more universal 'SELECT 1' via the SDK, we'll attempt a dummy table query 
            # or RPC if the user has defined it. 
            # Here we follow the logic from db_setup.py.
            supabase.rpc("exec_sql", {"sql_text": "SELECT 1"}).execute()
        except Exception as e:
            # Fallback ping if exec_sql isn't there
            try:
                supabase.table("articles").select("count", count="exact").limit(1).execute()
            except:
                warnings.append(f"Supabase connectivity check failed: {e}")

    # 3. Check SUBSTACK_COOKIE
    substack_cookie = os.getenv("SUBSTACK_COOKIE")
    if not substack_cookie:
        has_substack = any(s.get('type') == 'substack' for s in valid_sources)
        if has_substack:
            valid_sources = [s for s in valid_sources if s.get('type') != 'substack']
            warnings.append("SUBSTACK_COOKIE is missing. All 'substack' sources have been skipped.")

    return valid_sources, warnings

if __name__ == "__main__":
    print("Running preflight checks...")
    valid, warns = run_preflight()
    
    print(f"\nStatus: {len(valid)} sources ready for crawling.")
    
    if warns:
        print("\nWarnings/Errors encountered:")
        for w in warns:
            print(f"- {w}")
    
    if not valid and not warns:
        print("Everything looks good, but no sources found.")
