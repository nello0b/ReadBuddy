# app/models/image_extraction_result.py

from app.models.extraction_result import ExtractionResult
from azure.ai.documentintelligence.models import AnalyzeResult
import uuid
from typing import Optional, List

class ImageExtractionResult(ExtractionResult):
    def __init__(
        self,
        text_data: Optional[AnalyzeResult] = None,
        audio_zip_urls: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        category: Optional[str] = None,
        extraction_result: Optional[ExtractionResult] = None,
        id: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        if extraction_result is not None:
            super().__init__(
                text_data = extraction_result.text_data,
                audio_zip_urls = extraction_result.audio_zip_urls,
                category = extraction_result.category,
                id = extraction_result.id,
                created_at = extraction_result.created_at
            )
        else:
            _id = id if id else f"ier-{uuid.uuid4().hex[:12]}"
            super().__init__(text_data, audio_zip_urls, category, _id, created_at)
        self.file_path = file_path

    def to_dict(self):
        result_dict = super().to_dict()
        result_dict["file_path"] = self.file_path
        return result_dict