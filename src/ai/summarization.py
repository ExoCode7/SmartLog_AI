from rake_nltk import Rake
import nltk
from typing import List, Dict, Optional, Any

# Attempt to download data if not present
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("punkt")
    nltk.download("stopwords")


class KeywordEngine:
    def __init__(self, max_keywords: int = 5):
        self.rake = Rake(max_length=2)
        self.max_keywords = max_keywords

    def extract_keywords(self, text: str) -> List[str]:
        if not text.strip():
            return []
        self.rake.extract_keywords_from_text(text)
        return self.rake.get_ranked_phrases()[: self.max_keywords]

    def apply_user_guidance(
        self, keywords: List[str], instructions: Optional[Dict[str, Any]]
    ) -> List[str]:
        return keywords
