# app/services/azure/azure_ocr.py

from app.services.ocr_interface import OCRService
from config import AZURE_READ_KEY, AZURE_READ_ENDPOINT
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult

class AzureOCRService(OCRService):
    def __init__(self):
        self.client = DocumentIntelligenceClient(
            endpoint=AZURE_READ_ENDPOINT,
            credential=AzureKeyCredential(AZURE_READ_KEY)
        )

    def extract_text(self, image_path: str, lang: str = "auto") -> AnalyzeResult:
        with open(image_path, "rb") as f:
            image_data = f.read()

        poller = self.client.begin_analyze_document(
            "prebuilt-read",  # model_id as first positional argument
            AnalyzeDocumentRequest(bytes_source=image_data)  # request body as second positional argument
        )
        result: AnalyzeResult = poller.result()

        return result
