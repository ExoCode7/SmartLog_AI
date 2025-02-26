import pytest
from unittest.mock import MagicMock, patch
from src.ai.smart_summarizer import ISummarizer, SpacySummarizer, SmartSummarizerAdapter
import spacy


class MockSpacyToken:
    """Mock for a spaCy token."""

    def __init__(self, text, pos_="NOUN", dep_="nsubj", is_stop=False, lemma_=None):
        self.text = text
        self.pos_ = pos_
        self.dep_ = dep_
        self.is_stop = is_stop
        self.lemma_ = lemma_ or text.lower()
        self.children = []


class MockSpacySpan:
    """Mock for a spaCy span (e.g., noun chunk or entity)."""

    def __init__(self, text, tokens=None):
        self.text = text
        self._tokens = tokens or []

    def __len__(self):
        return len(self._tokens) if self._tokens else 1

    def __iter__(self):
        return iter(self._tokens)


class MockSpacyDoc:
    """Mock for a spaCy Doc object."""

    def __init__(self, text, ents=None, noun_chunks=None, tokens=None):
        self.text = text
        self.ents = ents or []
        self.noun_chunks = noun_chunks or []
        self.tokens = tokens or []

    def __iter__(self):
        return iter(self.tokens)


@pytest.fixture
def mock_nlp():
    """Create a mock spaCy nlp object."""
    mock = MagicMock()

    def process_text(text):
        # Create a simple mock document with some entities and noun chunks
        tokens = [
            MockSpacyToken("John", pos_="PROPN", dep_="nsubj"),
            MockSpacyToken("talked", pos_="VERB", dep_="ROOT"),
            MockSpacyToken("about", pos_="ADP", dep_="prep"),
            MockSpacyToken("the", pos_="DET", dep_="det", is_stop=True),
            MockSpacyToken("project", pos_="NOUN", dep_="pobj"),
            MockSpacyToken("yesterday", pos_="NOUN", dep_="npadvmod"),
        ]

        # Set up dependencies for verb phrases
        tokens[1].children = [tokens[0], tokens[2]]  # "talked" -> "John", "about"
        tokens[2].children = [tokens[4]]  # "about" -> "project"

        # Create entities
        entities = [
            MockSpacySpan("John", [tokens[0]]),
            MockSpacySpan("yesterday", [tokens[5]]),
        ]

        # Create noun chunks
        noun_chunks = [
            MockSpacySpan("John", [tokens[0]]),
            MockSpacySpan("the project", [tokens[3], tokens[4]]),
        ]

        return MockSpacyDoc(
            text=text, ents=entities, noun_chunks=noun_chunks, tokens=tokens
        )

    mock.side_effect = process_text
    return mock


@pytest.fixture
def spacy_summarizer(mock_nlp):
    """Create a SpacySummarizer with a mocked nlp object."""
    with patch("src.ai.smart_summarizer.spacy.load", return_value=mock_nlp):
        summarizer = SpacySummarizer(max_items_per_category=3)
        # Replace the nlp attribute directly to avoid calling spacy.load again
        summarizer.nlp = mock_nlp
        return summarizer


def test_summarizer_interface():
    """Test that ISummarizer defines the expected interface."""
    summarizer = ISummarizer()

    # Should raise NotImplementedError
    with pytest.raises(NotImplementedError):
        summarizer.summarize_conversation("Some text")

    # apply_user_guidance should return the input unchanged
    summary = {"keywords": ["test"]}
    assert summarizer.apply_user_guidance(summary, None) == summary


def test_spacy_summarizer_empty_text(spacy_summarizer):
    """Test that the summarizer handles empty text correctly."""
    result = spacy_summarizer.summarize_conversation("")

    assert isinstance(result, dict)
    assert "keywords" in result
    assert "entities" in result
    assert "actions" in result
    assert "topics" in result
    assert all(isinstance(v, list) for v in result.values())
    assert all(len(v) == 0 for v in result.values())


def test_spacy_summarizer_extracts_categories(spacy_summarizer):
    """Test that the summarizer extracts the expected categories from text."""
    text = "John talked about the project yesterday."
    result = spacy_summarizer.summarize_conversation(text)

    # Check that we have all expected categories
    assert isinstance(result, dict)
    assert set(result.keys()) == {"keywords", "entities", "actions", "topics"}

    # Check that each category contains the expected elements
    assert "the project" in result["keywords"]
    assert "John" in result["entities"]
    assert any("talked" in action for action in result["actions"])
    assert "project" in result["topics"] or "yesterday" in result["topics"]


def test_spacy_summarizer_apply_user_guidance(spacy_summarizer):
    """Test that user guidance is correctly applied to summaries."""
    # Create a sample summary
    summary = {
        "keywords": ["the project", "meeting schedule"],
        "entities": ["John", "Monday"],
        "actions": ["talked about", "scheduled"],
        "topics": ["project", "meeting", "schedule"],
    }

    # Test exclude_topics instruction
    instructions = {"exclude_topics": ["meeting"]}

    result = spacy_summarizer.apply_user_guidance(summary, instructions)

    # Check that items containing "meeting" are removed
    assert "meeting schedule" not in result["keywords"]
    assert "meeting" not in result["topics"]

    # Test detail_level instruction
    instructions = {"detail_level": "low"}

    result = spacy_summarizer.apply_user_guidance(summary, instructions)

    # Check that each category has at most 3 items
    assert all(len(items) <= 3 for items in result.values())


def test_smart_summarizer_adapter(spacy_summarizer):
    """Test that the adapter works correctly with the summarizer."""
    adapter = SmartSummarizerAdapter(spacy_summarizer)

    # Test with normal text
    text = "John talked about the project yesterday."
    keywords = adapter.extract_keywords(text)

    # Check that we get a list of keywords (not a dict)
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert "the project" in keywords

    # Test apply_user_guidance
    modified = adapter.apply_user_guidance(keywords, {"exclude_topics": ["project"]})
    assert "the project" not in modified


def test_summarizer_integration():
    """Test that the real SpacySummarizer works with real text."""
    # Only run this test if spaCy is properly installed
    try:
        # Verify spacy is working by checking its version
        spacy_version = spacy.__version__

        # Log the spaCy version being used for the test
        print(f"Running integration test with spaCy version {spacy_version}")

        # Skip if using a very old version of spaCy
        from packaging import version

        if version.parse(spacy_version) < version.parse("3.0.0"):
            pytest.skip(f"spaCy version {spacy_version} is too old for this test")

        summarizer = SpacySummarizer(max_items_per_category=3)

        text = (
            "The CEO announced a new product launch next month. "
            "The marketing team is preparing a campaign."
        )
        result = summarizer.summarize_conversation(text)

        # Basic validation of the result structure
        assert isinstance(result, dict)
        assert all(isinstance(v, list) for v in result.values())
        assert all(len(v) <= 3 for v in result.values())

        # The exact content depends on the spaCy model, but we can check some basics
        assert len(result["keywords"]) > 0
        assert len(result["entities"]) > 0

    except ImportError:
        pytest.skip("spaCy not installed, skipping integration test")
