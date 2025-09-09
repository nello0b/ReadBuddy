# app/models/glossary_entry.py

from typing import List
import uuid

class GlossaryEntry:
    def __init__(self,  
                 term: str, 
                 definition: str, 
                 term_audio_zip_urls: List[str] = None, 
                 definition_audio_zip_urls: List[str] = None,
                 user_id: int = None,
                 id: int = None):
        self.id = id if id else f"gt-{uuid.uuid4().hex[:12]}"
        self.user_id = user_id if user_id else ""
        self.term = term
        self.definition = definition
        self.term_audio_zip_urls = term_audio_zip_urls if term_audio_zip_urls else []
        self.definition_audio_zip_urls = definition_audio_zip_urls if definition_audio_zip_urls else []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "term": self.term,
            "definition": self.definition,
            "term_audio_zip_urls": self.term_audio_zip_urls,
            "definition_audio_zip_urls": self.definition_audio_zip_urls
        }
