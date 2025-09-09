# app/models/glossary.py

from typing import List, Dict
import uuid
from datetime import datetime, timezone
from app.models.glossary_entry import GlossaryEntry

class Glossary:
    def __init__(self,
                 category: str,
                 user_id: str = None,
                 id: str = None,
                 entries: List[GlossaryEntry] | None = None,
                 last_updated=None):
        """Initialize a glossary with a specific category."""
        self.category = category
        self.entries: List[GlossaryEntry] = entries if entries else []
        self.user_id = user_id if user_id else ""
        self.id = id if id else f"gl-{uuid.uuid4().hex[:12]}"
        self.last_updated = last_updated if last_updated else datetime.now(timezone.utc).isoformat()

    def add_entry(self, entry: GlossaryEntry) -> None:
        """Add a GlossaryEntry to the glossary."""
        self.entries.append(entry)
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def get_entry(self, term: str) -> GlossaryEntry:
        """Retrieve the GlossaryEntry for a term."""
        for entry in self.entries:
            if entry.term == term:
                return entry
        return None
    
    def update_entry(self, 
                     term: str, 
                     definition: str,
                     new_term_name: str = None,
                     term_audio_zip_urls: List[str] = None,
                     definition_audio_zip_urls: List[str] = None) -> None:
        """Update the definition of a term in the glossary."""
        entry = self.get_entry(term)
        if entry:
            entry.term = new_term_name if new_term_name else entry.term
            entry.definition = definition
            entry.term_audio_zip_urls = term_audio_zip_urls if term_audio_zip_urls else entry.term_audio_zip_urls
            entry.definition_audio_zip_urls = definition_audio_zip_urls if definition_audio_zip_urls else entry.definition_audio_zip_urls
            self.last_updated = datetime.now(timezone.utc).isoformat()
        else:
            raise ValueError(f"Term '{term}' not found in the glossary.")

    def get_definition(self, term: str) -> str:
        """Retrieve the definition of a term."""
        entry = self.get_entry(term)
        return entry.definition if entry else "Term not found."

    def remove_term(self, term: str) -> None:
        """Remove a term from the glossary."""
        self.entries = [entry for entry in self.entries if entry.term != term]
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def list_terms(self) -> List[str]:
        """List all terms in the glossary."""
        return [entry.term for entry in self.entries]
    
    @staticmethod
    def create_from_dict(glossary_dict: Dict[str,str], category: str = None, user_id = None) -> 'Glossary':
        """Create a Glossary object from a dictionary."""
        glossary = Glossary(category=category, user_id=user_id)
        for term, definition in glossary_dict.items():
            entry = GlossaryEntry(term=term, definition=definition)
            glossary.add_entry(entry)
        return glossary
        

    def to_dict(self) -> dict:
        """Serialize the glossary to a dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "user_id": self.user_id,
            "last_updated": self.last_updated,
            "entries": [entry.to_dict() for entry in self.entries]
        }
        
    def to_string(self) -> str:
        """Return a plain string representation of the glossary."""
        glossary_str = "Glossary:\n"
        for entry in self.entries:
            glossary_str += f"{entry.term}: {entry.definition}\n"
        return glossary_str