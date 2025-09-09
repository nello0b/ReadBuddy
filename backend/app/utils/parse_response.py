import json
import re
from typing import Dict, Any

def parse_json_or_key_value_fallback(content: str) -> Dict[str, Any]:
    """
    Try to parse a JSON object from a string. If that fails, fallback to key-value parsing.
    Accepts content with or without markdown formatting (```json).
    """
    if not content:
        raise ValueError("No content provided.")

    content = content.strip()

    # Remove markdown-style code fences
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    # Try parsing as JSON
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            parsed: Any = json.loads(json_match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass  # Try fallback below

    # Fallback: parse "Key: Value" or "Key - Value" lines
    result: Dict[str, Any] = {}
    for line in content.splitlines():
        line = line.strip().lstrip("-*• ")
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif "-" in line:
            key, value = line.split("-", 1)
        else:
            continue
        key, value = key.strip(), value.strip()
        if key and value:
            result[key] = value

    if not result:
        raise ValueError("Failed to parse content as JSON or key-value fallback.")

    return result
