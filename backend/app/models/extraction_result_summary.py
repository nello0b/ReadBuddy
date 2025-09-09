# app/models/extraction_result_summary.py

class ExtractionResultSummary:
    def __init__(self, extraction_id, created_at, category=None, title=None):
        self.extraction_id = extraction_id
        self.created_at = created_at
        self.category = category
        self.title = title[:20] if title else "Untitled"

    def to_dict(self):
        return {
            "extraction_id": self.extraction_id,
            "created_at": self.created_at,
            "category": self.category,
            "title": self.title,
        }
        