# app/services/language_interface.py

from abc import ABC, abstractmethod

class LanguageService(ABC):
    @abstractmethod
    def detect_language(self, text: str) -> str:
        """
        Detect the language of a given text string.

        Args:
            text (str): The input text for which to detect the language.

        Returns:
            str: The name of the detected language (e.g., "English", "French").
        """
        pass
