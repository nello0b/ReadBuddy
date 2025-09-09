import uuid
from typing import List
from datetime import datetime, timezone

class Summary:
    def __init__(self, source_ids: List[str], content: List[str], audio_zip_urls: List[str] = None, id: str = None, created_at: str = None):
        self.id = id if id else f"su-{uuid.uuid4().hex[:12]}"
        self.source_ids = source_ids if source_ids else []
        self.content = content
        self.audio_zip_urls = audio_zip_urls if audio_zip_urls else []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_ids": self.source_ids,
            "content": self.content,
            "audio_zip_urls": self.audio_zip_urls,
            "created_at": self.created_at,
        }
