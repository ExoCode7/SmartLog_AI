import spacy
from typing import List, Dict, Any, Optional, Union
import logging

# Load the logger
logger = logging.getLogger(__name__)


# Create interface class for summarizers
class ISummarizer:
    """Interface for text summarization engines."""

    def summarize_conversation(
        self, text: str
    ) -> Union[Dict[str, List[str]], Dict[str, Any]]:
        """
        Summarize the given text and return structured results.

        Args:
            text: The input text to summarize

        Returns:
            Dictionary with categorized summary elements
        """
        raise NotImplementedError("Subclasses must implement this method")

    def apply_user_guidance(
        self, summary: Dict[str, List[str]], instructions: Optional[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Apply user-specific instructions to customize the summary.

        Args:
            summary: The generated summary
            instructions: User-provided guidance for customization

        Returns:
            Modified summary based on user instructions
        """
        if not instructions:
            return summary

        # Handle excluding topics if specified
        if "exclude_topics" in instructions:
            excluded = instructions["exclude_topics"]
            return {
                category: [
                    item
                    for item in items
                    if not any(topic in item.lower() for topic in excluded)
                ]
                for category, items in summary.items()
            }

        return summary


class SpacySummarizer(ISummarizer):
    """
    Summarizer that uses spaCy for NLP processing to extract key information.
    """

    def __init__(
        self, model_name: str = "en_core_web_sm", max_items_per_category: int = 5
    ):
        """
        Initialize the SpaCy-based summarizer.

        Args:
            model_name: Name of the spaCy model to use
            max_items_per_category: Maximum number of items to include in each category
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"Model {model_name} not found. Downloading...")
            try:
                spacy.cli.download(model_name)
                self.nlp = spacy.load(model_name)
                logger.info(f"Downloaded and loaded spaCy model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                # Fallback to blank model as last resort
                self.nlp = spacy.blank("en")
                logger.warning("Using blank English model as fallback")

        self.max_items = max_items_per_category

    def summarize_conversation(self, text: str) -> Dict[str, List[str]]:
        """
        Create a structured summary of the input text using spaCy.

        Returns a dictionary with these categories:
        - keywords: Important concepts/terms
        - entities: Named entities (people, orgs, locations, etc.)
        - actions: Key verbs/actions mentioned
        - topics: Main topics or themes
        """
        if not text.strip():
            return {"keywords": [], "entities": [], "actions": [], "topics": []}

        # Process the text with spaCy
        doc = self.nlp(text)

        # Extract entities
        entities = []
        for ent in doc.ents:
            if ent.text.strip() and ent.text not in entities:
                entities.append(ent.text)

        # Extract key noun chunks as keywords
        keywords = []
        for chunk in doc.noun_chunks:
            # Filter meaningful chunks (longer than 1 token, not just determiners, etc.)
            if len(chunk) > 1 and not all(token.is_stop for token in chunk):
                clean_text = chunk.text.strip()
                if clean_text and clean_text not in keywords:
                    keywords.append(clean_text)

        # Extract main verbs as actions
        actions = []
        for token in doc:
            if token.pos_ == "VERB" and not token.is_stop:
                # Get the verb with its object if available
                if token.dep_ in ("ROOT", "xcomp"):
                    verb_phrase = self._get_verb_phrase(token)
                    if verb_phrase and verb_phrase not in actions:
                        actions.append(verb_phrase)

        # For topics, we'll use a simple frequency-based approach
        # In a real implementation, you might use topic modeling algorithms
        topics = self._extract_topics(doc)

        # Limit the number of items in each category
        return {
            "keywords": keywords[: self.max_items],
            "entities": entities[: self.max_items],
            "actions": actions[: self.max_items],
            "topics": topics[: self.max_items],
        }

    def _get_verb_phrase(self, verb_token) -> str:
        """Extract a verb phrase including the verb and its direct objects."""
        phrase = verb_token.text

        # Get direct objects
        objects = [
            child.text
            for child in verb_token.children
            if child.dep_ in ("dobj", "pobj") and not child.is_stop
        ]

        if objects:
            phrase += " " + " ".join(objects)

        return phrase.strip()

    def _extract_topics(self, doc) -> List[str]:
        """Extract main topics from the document based on noun frequency."""
        # Count noun frequencies
        noun_freq = {}
        for token in doc:
            if token.pos_ in ("NOUN", "PROPN") and not token.is_stop:
                noun_freq[token.lemma_] = noun_freq.get(token.lemma_, 0) + 1

        # Sort by frequency
        sorted_nouns = sorted(noun_freq.items(), key=lambda x: x[1], reverse=True)

        # Return top nouns as topics
        return [noun for noun, _ in sorted_nouns[: self.max_items]]

    def apply_user_guidance(
        self,
        summary: Dict[str, List[str]],
        instructions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[str]]:
        """
        Apply user guidance to customize the summary.

        Args:
            summary: The generated summary
            instructions: User instructions that might include:
                - focus_areas: List of areas to emphasize
                - exclude_topics: List of topics to exclude
                - detail_level: 'high', 'medium', or 'low'

        Returns:
            Modified summary based on user instructions
        """
        if not instructions:
            return summary

        # Example of applying instructions (simplified)
        result = dict(summary)

        # Filter out excluded topics if specified
        if "exclude_topics" in instructions:
            for category in result:
                result[category] = [
                    item
                    for item in result[category]
                    if not any(
                        topic.lower() in item.lower()
                        for topic in instructions["exclude_topics"]
                    )
                ]

        # Adjust detail level
        if "detail_level" in instructions:
            detail_level = instructions["detail_level"]
            if detail_level == "low":
                # Reduce number of items
                for category in result:
                    result[category] = result[category][: min(3, len(result[category]))]
            elif detail_level == "high":
                # Keep everything (already at max_items)
                pass

        return result


# Create a backward compatible summarizer that works with the old interface
class SmartSummarizerAdapter:
    """
    Adapter that wraps a SpacySummarizer to provide backward compatibility
    with the KeywordEngine interface.
    """

    def __init__(self, summarizer: ISummarizer):
        """Initialize with a SpacySummarizer instance."""
        self.summarizer = summarizer

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text using the wrapped summarizer.

        This method maintains compatibility with the KeywordEngine interface
        while leveraging the more advanced SpacySummarizer backend.
        """
        result = self.summarizer.summarize_conversation(text)
        return result.get("keywords", [])

    def summarize(self, text: str) -> Dict[str, Any]:
        """
        Compatibility method with the old interface.
        Returns just the keywords for backward compatibility.
        """
        result = self.summarizer.summarize_conversation(text)
        return {"keywords": result.get("keywords", [])}

    def apply_user_guidance(self, keywords, instructions):
        """
        Apply user-specific instructions to customize the keywords.

        Args:
            keywords: The list of extracted keywords
            instructions: User-provided guidance for customization

        Returns:
            Modified keywords based on user instructions
        """
        if not instructions:
            return keywords

        # Handle excluding topics if specified
        if "exclude_topics" in instructions:
            excluded = instructions["exclude_topics"]
            return [
                keyword
                for keyword in keywords
                if not any(topic in keyword.lower() for topic in excluded)
            ]

        return keywords
