import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class KeywordEngine:
    """
    Simple keyword extraction engine for text summarization.
    Provides a fallback when SpacySummarizer is unavailable.
    """

    def __init__(self):
        logger.info("Initializing KeywordEngine")
        # Common stop words to exclude
        self.stop_words = {
            "the",
            "a",
            "an",
            "and",
            "in",
            "on",
            "at",
            "to",
            "for",
            "is",
            "are",
            "was",
            "were",
            "be",
            "have",
            "has",
            "had",
            "this",
            "that",
            "there",
            "their",
            "they",
            "it",
            "of",
            "with",
        }

    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text using basic frequency analysis."""
        if not text:
            return []

        # Simple implementation - split by spaces and get most common words
        words = [
            word.lower()
            for word in text.split()
            if word.lower() not in self.stop_words and len(word) > 3
        ]

        # Count occurrences
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]

    def summarize(self, text: str) -> Dict[str, Any]:
        """Compatibility method with the ISummarizer interface."""
        keywords = self.extract_keywords(text)
        return {"keywords": keywords}
