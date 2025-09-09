# app/services/ocr_interface.py

from abc import ABC, abstractmethod
from azure.ai.documentintelligence.models import AnalyzeResult

class OCRService(ABC):
    @abstractmethod
    def extract_text(self, image_path: str, lang: str = "auto") -> AnalyzeResult:
        """
        Extract text and raw data from an image.

        Returns:
            OCRResult: Contains extracted plain text and full raw OCR response.
        """
        pass
