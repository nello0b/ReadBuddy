# app/models/answer.py

from typing import List
import uuid

class Answer:
    """
    Represents an answer in a quiz, containing the user's response and associated audio files.
    """
    def __init__(self, user_id: str, content: str, audio_zip_urls: List[str] = None, id :str = None):
        self.user_id = user_id
        self.id = f"a-{uuid.uuid4().hex[:12]}" if not id else id
        self.content = content
        self.audio_zip_urls = audio_zip_urls if audio_zip_urls else []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "audio_zip_urls": self.audio_zip_urls
        }