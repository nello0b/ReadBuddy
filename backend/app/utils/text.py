from typing import List
import re


def split_text_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs after every newline and ignore blank lines."""
    # Split by newline and filter out empty lines
    paragraphs = [line.strip() for line in text.split("\n") if line.strip()]
    return paragraphs

