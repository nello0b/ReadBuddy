# backend/app/services/__init__.py

from app.services.azure.azure_ocr import AzureOCRService
from app.services.azure.azure_tts import AzureTTSService
from app.services.azure.azure_language import AzureLanguageService
from app.services.azure.azure_gpt import AzureGPTService

ocr_service = AzureOCRService()
tts_service = AzureTTSService()
language_service = AzureLanguageService()
gpt_service = AzureGPTService()
