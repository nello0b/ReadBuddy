# database/interface.py

from app.models.extraction_result import ExtractionResult
from app.models.image_extraction_result import ImageExtractionResult
from app.models.user import User
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.answer import Answer
from app.models.glossary import Glossary
from app.models.glossary_entry import GlossaryEntry
from app.models.summary import Summary
from typing import List, Tuple

class DatabaseInterface:
    def get_user_by_sub(self, sub: str):
        raise NotImplementedError

    def create_user(self, user: User):
        raise NotImplementedError

    def save_image_extraction_result(self, extraction_result: ImageExtractionResult, user_id: str):
        raise NotImplementedError
    
    def save_extraction_result(self, extraction_result: ExtractionResult, user_id: str):
        raise NotImplementedError
    
    def ping_database(self):
        raise NotImplementedError
    
    def get_all_extraction_results_summary(self, user_id: str) -> List[str]:
        raise NotImplementedError
    
    # returns the extraction result and the media path
    def get_extraction_result_by_id(self, extraction_id: str, user_id: str) -> Tuple[ExtractionResult, str]:
        raise NotImplementedError
    
    def get_image_extraction_result_by_id(self, extraction_id: str, user_id: str) -> ImageExtractionResult:
        raise NotImplementedError
    
    def get_image_extraction_results_by_ids(self, extraction_ids: List[str], user_id: str) -> List[ImageExtractionResult]:
        raise NotImplementedError
    
    
    def get_extraction_results_by_ids(self, extraction_ids: List[str], user_id: str) -> List[Tuple[ExtractionResult, str]]:
        raise NotImplementedError
    
    def get_extraction_results_by_category(self, category: str, user_id: str) -> List[ImageExtractionResult]:
        raise NotImplementedError
    
    def update_extraction_results_category(self, new_category: str,  extraction_id: str, user_id: str) -> bool:
        raise NotImplementedError
    
    def get_user_categories(self,  user_id: str) -> List[str]:
        raise NotImplementedError
    
    def save_quiz(self, quiz: Quiz):
        raise NotImplementedError
    
    def get_quiz_by_id(self, quiz_id: str, user_id: str) -> Quiz:
        raise NotImplementedError
    
    def get_quizzes_by_user_id(self, user_id: str) -> List[Quiz]:
        raise NotImplementedError
    
    def get_question_by_id(self, question_id: str, user_id: str) -> Question:
        raise NotImplementedError
    
    def get_questions_by_ids(self, question_ids: List[str], user_id: str) -> List[Question]:
        raise NotImplementedError
    
    def save_questions(self, questions: List[Question], user_id: str):
        raise NotImplementedError
    
    def save_question(self, question: Question, user_id: str):
        raise NotImplementedError
    
    def update_question(self, question: Question, user_id: str):
        raise NotImplementedError
    
    def get_quizzes_by_category(self, category: str, user_id: str) -> List[Quiz]:
        raise NotImplementedError
    
    def save_glossary(self, glossary: Glossary, user_id: str):
        raise NotImplementedError
    
    def update_glossary_entry(self, entry: GlossaryEntry, user_id: str):
        """Update an existing glossary for a user."""
        raise NotImplementedError
    
    def get_glossary_by_id(self, glossary_id: str, user_id: str) -> Glossary:
        raise NotImplementedError

    def get_all_glossaries(self, user_id: str) -> List[Glossary]:
        raise NotImplementedError

    def delete_image_extraction_result(self, extraction_id: str, user_id: str) -> bool:
        """Delete an image extraction result for a user."""
        raise NotImplementedError

    def delete_quiz(self, quiz_id: str, user_id: str) -> bool:
        """Delete a quiz and its related data for a user."""
        raise NotImplementedError

    def delete_question(self, question_id: str, user_id: str) -> bool:
        """Delete a question and its related answers for a user."""
        raise NotImplementedError

    def delete_answer(self, answer_id: str, user_id: str) -> bool:
        """Delete an answer for a user."""
        raise NotImplementedError

    def save_summary(self, summary: Summary, user_id: str):
        raise NotImplementedError

    def get_summary_by_id(self, summary_id: str, user_id: str) -> Summary:
        raise NotImplementedError

    def delete_summary(self, summary_id: str, user_id: str) -> bool:
        raise NotImplementedError

    def update_summary(self, summary: Summary, user_id: str):
        raise NotImplementedError

    def get_summaries_by_user_id(self, user_id: str) -> List[Summary]:
        raise NotImplementedError

    def get_summaries_by_source_id(self, source_id: str, user_id: str) -> List[Summary]:
        raise NotImplementedError
    
    def save_task_state(self, task_id: str, status: str, meta: dict):
        raise NotImplementedError
    
    def get_task_status(self, task_id: str) -> dict:
        raise NotImplementedError
    
    def plan_database_empty(self, secret: str, keep_collections: List[str]) -> dict:
        """Plan what collections will be dropped without actually dropping them."""
        raise NotImplementedError
    
    def execute_database_empty(self, plan: dict):
        """Execute the database empty plan with confirmation token."""
        raise NotImplementedError