# backend/app/utils/language.py

from app.services import language_service

def detect_language_from_text(text: str, country_hint: str = "us") -> str:
    return language_service.detect_language(text, country_hint)
