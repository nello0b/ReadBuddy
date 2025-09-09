# app/services/gpt_interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.glossary import Glossary

class GPTService(ABC):
    @abstractmethod
    def classify(self, input_text: str, categories: List[str], lang: str, max_length: int) -> str:
        """Classify text into a category."""
        pass

    @abstractmethod
    def extract_glossary(self, article_texts: List[str], lang: str, max_tokens: int) -> Dict[str, str]:
        """Extract a glossary from the given article texts."""
        pass

    @abstractmethod
    def generate_questions(
        self,
        article_texts: List[str],
        lang: str,
        glossary: Glossary = None,
        number_of_questions: int = 10,
        one_shot_examples_to_use: int = 1,
        with_evaluation: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate questions based on the supplied texts and glossary.

        Args:
            article_texts (List[str]): The article texts to use when generating
                the questions.
            lang (str): The language to use for generation.
            glossary (Glossary, optional): The glossary extracted from the articles.
            number_of_questions (int, optional): How many questions to generate.
            one_shot_examples_to_use (int, optional): How many one-shot examples to
                provide the model with.
            with_evaluation (bool, optional): Whether to evaluate questions before returning.
        """
        pass

    @abstractmethod
    def create_summary(self, article_texts: List[str], lang: str) -> str:
        """Create a summary for the provided article texts."""
        pass
