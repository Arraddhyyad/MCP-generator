import json
from typing import List, Any, Union

def safe_string_processing(items: Union[List[str], List[Any], str, None], to_lower=True) -> List[str]:
    """Safely convert various input types to a list of clean strings."""
    if not items:
        return []

    if isinstance(items, str):
        return [item.strip().lower() if to_lower else item.strip() for item in items.split(',') if item and item.strip()]

    if isinstance(items, list):
        processed = []
        for item in items:
            if item is None:
                continue
            if isinstance(item, str):
                processed.append(item.strip().lower() if to_lower else item.strip())
            elif isinstance(item, dict):
                if 'name' in item:
                    processed.append(str(item['name']).strip().lower() if to_lower else str(item['name']).strip())
                else:
                    processed.append(json.dumps(item).lower() if to_lower else json.dumps(item))
            else:
                processed.append(str(item).lower() if to_lower else str(item))
        return [item for item in processed if item]

    return []
