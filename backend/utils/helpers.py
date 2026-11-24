import json
from typing import Any, List, Optional
from backend.database.schemas import SourceReference

def serialize_sources(sources: Optional[List[SourceReference]]) -> Optional[str]:
    """Serializes a list of SourceReference objects to a JSON string."""
    if not sources:
        return None
    return json.dumps([s.model_dump() for s in sources], ensure_ascii=False)

def deserialize_sources(sources_json: Optional[str]) -> List[SourceReference]:
    """Deserializes a JSON string into a list of SourceReference objects."""
    if not sources_json:
        return []
    try:
        data = json.loads(sources_json)
        return [SourceReference(**item) for item in data]
    except Exception:
        return []
