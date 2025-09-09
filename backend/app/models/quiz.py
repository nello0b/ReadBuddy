# app/models/quiz.py

from typing import List
import uuid
from datetime import datetime, timezone

class Quiz:
    """
    Represents a quiz containing multiple questions.
    """
    def __init__(
        self,
        user_id: str,  # Changed to str for consistency
        title: str,
        category: str,
        question_ids: List[str],  # Renamed for clarity
        id: str = None,
        created_at: str = None,
    ):
        self.title = title
        self.user_id = user_id
        self.category = category
        self.id = f"qz-{uuid.uuid4().hex[:12]}" if not id else id
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.question_ids = question_ids

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "category": self.category,
            "question_ids": self.question_ids,
            "created_at": self.created_at
        }
