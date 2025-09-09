# app/models/question.py

from typing import List
from app.models.answer import Answer
import uuid

class Question:
    """
    Represents a question in a quiz, containing multiple answers and the correct answer.
    """
    def __init__(
        self,
        user_id: str,
        content: str,
        answers: List[Answer],
        correct_answer_id: str,
        audio_zip_urls: List[str] = None,
        id: str = None
    ):
        self.user_id = user_id
        self.id = f"q-{uuid.uuid4().hex[:12]}" if not id else id
        self.content = content
        self.answers = answers
        self.correct_answer_id = correct_answer_id
        self.audio_zip_urls = audio_zip_urls if audio_zip_urls else []
        
    @staticmethod
    def from_dict(user_id: str, data: dict) -> "Question":
        """
        Static method to create a Question object from a dictionary.
        """
        options_dict = data["options"]
        correct_option_letter = data["correct_answer"]
        answers = []
        correct_answer_id = None

        for letter, content in options_dict.items():
            answer = Answer(user_id=user_id, content=content)
            if letter == correct_option_letter:
                correct_answer_id = answer.id
            answers.append(answer)

        return Question(
            user_id=user_id,
            content=data["question"],
            answers=answers,
            correct_answer_id=correct_answer_id
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "answers": [answer.to_dict() for answer in self.answers],
            "correct_answer_id": self.correct_answer_id,
            "audio_zip_urls": self.audio_zip_urls
        }