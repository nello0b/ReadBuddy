# backend/app/utils/ssml.py

from typing import List
from xml.etree.ElementTree import Element, SubElement
import html
from azure.ai.documentintelligence.models import AnalyzeResult
from app.models.question import Question
from app.utils.text import split_text_into_paragraphs

def analyze_result_to_ssml_chunks(
    analyze_result: AnalyzeResult,
    voice: str = "en-US-JennyNeural",
    rate: str = "1.0"
) -> List[Element]:
    """
    Convert AnalyzeResult into a list of SSML <speak> XML Elements, one per paragraph.
    """
    if not analyze_result.paragraphs:
        raise ValueError("No paragraphs found in AnalyzeResult")

    ssml_chunks = []

    for para in analyze_result.paragraphs:
        content = para.content.strip()
        
        speak = Element("speak", {
            "version": "1.0",
            "xmlns": "http://www.w3.org/2001/10/synthesis",
            "xmlns:mstts": "https://www.w3.org/2001/mstts",
            "xml:lang": "en-US"
        })
        
        if not content:
            # add an empty speak element if the paragraph is empty
            ssml_chunks.append(speak)
            continue

        voice_el = SubElement(speak, "voice", {"name": voice})
        prosody_el = SubElement(voice_el, "prosody", {"rate": rate})
        p_el = SubElement(prosody_el, "p")
        # Escape only the minimal set of characters required for SSML
        # to prevent double-encoding of apostrophes and quotes.
        p_el.text = html.escape(content, quote=False)

        ssml_chunks.append(speak)

    return ssml_chunks

def question_to_ssml_chunks(
    question: Question,
    voice: str = "en-US-JennyNeural",
    rate: str = "1.0"
) -> List[Element]:
    """
    Convert a Question object into a list of SSML <speak> XML Elements, one for the question and one for each answer.
    """

    ssml_chunks: List[Element] = []

    question_text = question.content.strip()
    if question_text:
        speak_q = Element("speak", {
                "version": "1.0",
                "xmlns": "http://www.w3.org/2001/10/synthesis",
                "xmlns:mstts": "https://www.w3.org/2001/mstts",
                "xml:lang": "en-US"
            })
        voice_el = SubElement(speak_q, "voice", {"name": voice})
        prosody_el = SubElement(voice_el, "prosody", {"rate": rate})
        p_el = SubElement(prosody_el, "p")
        # Avoid escaping apostrophes or quotes to ensure natural speech
        p_el.text = html.escape(question_text, quote=False)
        ssml_chunks.append(speak_q)

    for answer in question.answers:
        answer_text = answer.content.strip()
        if not answer_text:
            continue

        speak_a = Element("speak", {
                "version": "1.0",
                "xmlns": "http://www.w3.org/2001/10/synthesis",
                "xmlns:mstts": "https://www.w3.org/2001/mstts",
                "xml:lang": "en-US"
            })
        voice_el_a = SubElement(speak_a, "voice", {"name": voice})
        prosody_el_a = SubElement(voice_el_a, "prosody", {"rate": rate})
        p_el_a = SubElement(prosody_el_a, "p")
        # Preserve natural punctuation in answers as well
        p_el_a.text = html.escape(answer_text, quote=False)
        ssml_chunks.append(speak_a)

    return ssml_chunks

def text_to_ssml_chunks(paragraphs: List[str], voice: str = "en-US-JennyNeural", rate: str = "1.0") -> List[Element]:
    ssml_chunks: List[Element] = []
    for para in paragraphs:
        speak = Element(
            "speak",
            {
                "version": "1.0",
                "xmlns": "http://www.w3.org/2001/10/synthesis",
                "xmlns:mstts": "https://www.w3.org/2001/mstts",
                "xml:lang": "en-US",
            },
        )
        voice_el = SubElement(speak, "voice", {"name": voice})
        prosody_el = SubElement(voice_el, "prosody", {"rate": rate})
        p_el = SubElement(prosody_el, "p")
        p_el.text = html.escape(para, quote=False)
        ssml_chunks.append(speak)
    return ssml_chunks

