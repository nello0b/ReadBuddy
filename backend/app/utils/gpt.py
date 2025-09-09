# backend/app/utils/gpt.py

from app.services import gpt_service
from typing import List
from app.utils.language import detect_language_from_text
from app.models.glossary import Glossary



def classify_text(input_text: str, categories: List[str] = None, lang: str = "auto", max_length: int = 20) -> str:
    # detect language if not provided
    if lang == "auto":
        lang = detect_language_from_text(input_text)
        
    # number of attempts to classify
    try:
        category = gpt_service.classify(input_text, categories, lang, max_length)
        return category
    except Exception as e:
        print(f"Error during classification: {e}")
        return "Cannot Be Classified"

def extract_glossary(articles: List[str], category : str = None, lang: str = "auto", with_audio = False) -> Glossary:
    
    # detect language if not provided
    if lang == "auto":
        lang = detect_language_from_text(" ".join(articles))
        
    
    # Extract glossary using the GPT service
    # number of attempts to classify
    attempts = 3
    while True:
        try:
            glossary_dict = gpt_service.extract_glossary(article_texts=articles,
                                                         lang=lang)
            break
        except Exception as e:
            print(f"Error during glossary extraction: {e}")
            attempts -= 1
            if attempts <= 0:
                print("Failed to extract glossary after multiple attempts.")
                raise RuntimeError("Failed to extract glossary after multiple attempts.")
    
    
    
    glossary = Glossary.create_from_dict(glossary_dict, category=category)
    
    return glossary