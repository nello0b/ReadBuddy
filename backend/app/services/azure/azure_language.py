# app/services/azure/azure_language.py

from azure.ai.textanalytics import TextAnalyticsClient
from app.services.language_interface import LanguageService
from azure.core.credentials import AzureKeyCredential
from config import AZURE_LANGUAGE_KEY, AZURE_LANGUAGE_ENDPOINT

LENGTH_LIMIT = 5120  # Azure Text Analytics has a limit of 5120 characters per document

class AzureLanguageService(LanguageService):
    def __init__(self):
        if not AZURE_LANGUAGE_KEY or not AZURE_LANGUAGE_ENDPOINT:
            raise ValueError("Azure language key or endpoint not configured.")

        self.client = TextAnalyticsClient(
            endpoint=AZURE_LANGUAGE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_LANGUAGE_KEY)
        )

    def detect_language(self, text: str, country_hint: str = "us") -> str:
        try:
            response = self.client.detect_language(
                documents=[text[:LENGTH_LIMIT]], # Truncate text to fit Azure's limit
                country_hint=country_hint
            )[0]

            if response.is_error:
                raise Exception(f"Language detection error: {response.error}")

            return response.primary_language.name
        except Exception as e:
            print(f"❌ Language detection failed: {e}")
            return "unknown"
