import json
import os
from jsonschema import validate, ValidationError

# Schema for a single source object
SOURCE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "url": {"type": "string"},
        "type": {"enum": ["rss", "substack", "scrape"]},
        "tags": {"type": "array", "items": {"type": "string"}},
        "css_selector": {"type": "string"}
    },
    "required": ["name", "url", "type", "tags"],
    "if": {
        "properties": {"type": {"const": "scrape"}}
    },
    "then": {
        "required": ["css_selector"]
    },
    "else": {
        "not": {"required": ["css_selector"]}
    }
}

# Schema for the entire sources list
SCHEMA = {
    "type": "array",
    "items": SOURCE_SCHEMA
}

def validate_sources(config_path=None):
    """
    Load the sources JSON and validate it against the schema.
    Returns the list of valid sources if successful.
    Raises ValueError with descriptive details if validation fails.
    """
    if config_path is None:
        # Default to the expected location relative to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config", "sources.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {config_path}: {e}")

    try:
        validate(instance=data, schema=SCHEMA)
        return data
    except ValidationError as e:
        # Identify which entry failed
        if e.path:
            index = e.path[0]
            if isinstance(index, int) and index < len(data):
                source_identifier = data[index].get('name', f'at index {index}')
                error_msg = f"Validation failed for source '{source_identifier}': {e.message}"
            else:
                error_msg = f"Validation error: {e.message}"
        else:
            error_msg = f"Validation error: {e.message}"
        
        raise ValueError(error_msg)

if __name__ == "__main__":
    try:
        sources = validate_sources()
        print(f"Validation successful. Loaded {len(sources)} sources.")
        for s in sources:
            print(f"- {s['name']} ({s['type']})")
    except Exception as e:
        print(f"Validation failed: {e}")
        exit(1)
