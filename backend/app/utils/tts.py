# backend/app/utils/tts.py

from app.services import tts_service
from azure.ai.documentintelligence.models import AnalyzeResult
from app.utils.ssml import (
    analyze_result_to_ssml_chunks,
    question_to_ssml_chunks,
    text_to_ssml_chunks
)
from app.utils.language import detect_language_from_text
from xml.etree.ElementTree import Element
from typing import List, Optional
from config import DEBUG_MODE
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.glossary_entry import GlossaryEntry
import time
import asyncio

async def synthesize_speech_from_analyzeresult(result: AnalyzeResult, voice: str = "en-US-AriaNeural", rate: str = "1", lang: str = "auto") -> Optional[List[str]]:
    if not lang or lang == "auto":
        detect_language_start_time = time.time() if DEBUG_MODE else None
        lang = detect_language_from_text(result.get("content", ""))
        if DEBUG_MODE:
            detect_language_end_time = time.time()
            print(f"⏰ Language detection completed in {detect_language_end_time - detect_language_start_time:.2f} seconds")
    
    if lang == "Hebrew":
        voice = "he-IL-HilaNeural"   

    # Generate SSML chunks from the AnalyzeResult
    ssml_chunks: List[Element] = analyze_result_to_ssml_chunks(result, voice, rate)
    
    synthesize_multi_start_time = time.time() if DEBUG_MODE else None
    
    zip_paths = await tts_service.synthesize_multi(ssml_chunks, voice)
    
    if DEBUG_MODE:
        synthesize_multi_end_time = time.time()
        print(f"⏰ TTS synthesis completed in {synthesize_multi_end_time - synthesize_multi_start_time:.2f} seconds")
    
    return zip_paths if zip_paths else None

async def synthesize_question_speech(
    question: Question,
    lang: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "1"
) -> Optional[List[str]]:
    """Synthesize speech for a single question and its answers."""
    if lang == "Hebrew":
        voice = "he-IL-HilaNeural"

    ssml_chunks: List[Element] = question_to_ssml_chunks(question, voice, rate)

    if not ssml_chunks:
        return []

    if DEBUG_MODE:
        synthesize_multi_start_time = time.time()

    zip_paths = await tts_service.synthesize_multi(ssml_chunks, voice)

    if DEBUG_MODE:
        synthesize_multi_end_time = time.time()
        print(
            f"⏰ TTS synthesis completed in {synthesize_multi_end_time - synthesize_multi_start_time:.2f} seconds"
        )

    return zip_paths if zip_paths else None

async def synthesize_summary_speech(
    paragraphs: List[str],
    lang: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "1"
) -> Optional[List[str]]:
    if lang == "auto" or not lang:
        lang = detect_language_from_text(" ".join(paragraphs))
    if lang == "Hebrew":
        voice = "he-IL-HilaNeural"
    ssml_chunks: List[Element] = text_to_ssml_chunks(paragraphs, voice, rate)
    if not ssml_chunks:
        return []

    if DEBUG_MODE:
        synthesize_multi_start_time = time.time()

    zip_paths = await tts_service.synthesize_multi(ssml_chunks, voice)

    if DEBUG_MODE:
        synthesize_multi_end_time = time.time()
        print(
            f"⏰ TTS synthesis completed in {synthesize_multi_end_time - synthesize_multi_start_time:.2f} seconds"
        )

    return zip_paths if zip_paths else None


async def synthesize_glossary_entry_speech(
    entry: GlossaryEntry,
    lang: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "1",
) -> Optional[List[str]]:
    """Synthesize speech for a glossary entry term and definition."""
    if lang == "Hebrew":
        voice = "he-IL-HilaNeural"

    texts: List[str] = []
    if entry.term and entry.term.strip():
        texts.append(entry.term.strip())
    if entry.definition and entry.definition.strip():
        texts.append(entry.definition.strip())

    if not texts:
        return []

    ssml_chunks: List[Element] = text_to_ssml_chunks(texts, voice, rate)

    if DEBUG_MODE:
        synthesize_multi_start_time = time.time()

    zip_paths = await tts_service.synthesize_multi(ssml_chunks, voice)

    if DEBUG_MODE:
        synthesize_multi_end_time = time.time()
        print(
            f"⏰ TTS synthesis completed in {synthesize_multi_end_time - synthesize_multi_start_time:.2f} seconds"
        )

    return zip_paths if zip_paths else None
        
    
