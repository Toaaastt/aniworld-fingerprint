from typing import Any
import json
import os

def read_json_file(filepath: str = 'database.json') -> Any | dict:
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def write_json_file(data, filepath: str = 'database.json') -> str | None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
