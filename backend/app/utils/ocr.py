# backend/app/utils/ocr.py

from app.services import ocr_service
from azure.ai.documentintelligence.models import AnalyzeResult

def extract_text_from_image(image_path: str, lang: str = "auto") -> AnalyzeResult:
    return ocr_service.extract_text(image_path, lang=lang)
