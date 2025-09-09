# app/models/extraction_result.py

from azure.ai.documentintelligence.models import AnalyzeResult
import uuid
from typing import List
from datetime import datetime, timezone

class ExtractionResult:
    def __init__(self,
                 text_data: AnalyzeResult,
                 audio_zip_urls: List[str],
                 category: str = None,
                 id: str = None,
                 created_at: str = None):
        self.id = f"er-{uuid.uuid4().hex[:12]}" if not id else id
        self.text_data = text_data
        self.audio_zip_urls = audio_zip_urls
        self.category = category
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "text_data": self.text_data,
            "audio_zip_urls": self.audio_zip_urls,
            "category": self.category,
            "id": self.id,
            "created_at": self.created_at
        }
        