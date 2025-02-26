import spacy
from typing import List, Dict


class SpacySummarizer:
    """
    A summarizer that uses spaCy to extract keywords and entities.
    """

    def __init__(self, max_items_per_category: int = 5):
        self.nlp = spacy.load("en_core_web_sm")
        self.max_items = max_items_per_category

    def summarize_conversation(self, text: str) -> Dict[str, List[str]]:
        """
        Summarizes the conversation by extracting keywords and entities.
        Args:
            text: The conversation text.
        Returns:
            A dictionary with 'keywords' and 'entities'.
        """
        doc = self.nlp(text)
        keywords = [
            token.text for token in doc if token.is_alpha and not token.is_stop
        ][: self.max_items]
        entities = [ent.text for ent in doc.ents][: self.max_items]
        return {"keywords": keywords, "entities": entities}
