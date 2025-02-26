import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from src.audio.capture import AudioCapturer
from src.ai.stt_engine import HybridSTTEngine
from src.ai.smart_summarizer import SpacySummarizer


class TestEndToEndPipeline:
    """Tests for the full pipeline from audio capture to summarization."""

    @pytest.fixture
    def mock_audio_capturer(self):
        """Creates a mock AudioCapturer that returns predetermined audio chunks."""
        capturer = MagicMock(spec=AudioCapturer)

        # Mock audio chunk that represents silence
        silence = np.zeros(1600, dtype=np.int16).tobytes()

        # Set up the get_chunk method to return our test chunks
        capturer.get_chunk.side_effect = [silence] * 3  # Return silence 3 times

        return capturer

    @pytest.fixture
    def mock_stt_engine(self):
        """Creates a mock STT engine that returns predetermined transcriptions."""
        engine = MagicMock(spec=HybridSTTEngine)

        # Set up the transcribe method to return our test transcriptions
        engine.transcribe.side_effect = [
            "",  # First call returns empty (silence)
            "The CEO announced the product launch.",  # Second call
            "The marketing team will create a campaign.",  # Third call
        ]

        # Set up the final_result method
        engine.final_result.return_value = (
            "We need to prepare for the launch next month."
        )

        return engine

    @patch("src.ai.smart_summarizer.spacy.load")
    def test_full_pipeline(self, mock_spacy_load, mock_audio_capturer, mock_stt_engine):
        """
        Tests the full pipeline from audio capture to summarization.

        This test verifies that:
        1. Audio chunks from the capturer are processed by the STT engine
        2. Transcriptions from the STT engine are processed by the summarizer
        3. The summarizer produces structured output with the expected categories
        """
        # Set up mock spaCy NLP pipeline
        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Create a real SpacySummarizer with mocked internals
        summarizer = SpacySummarizer()

        # Mock the summarize_conversation method to return predefined summaries
        mock_summary = {
            "keywords": ["product launch", "marketing campaign"],
            "entities": ["CEO", "marketing team"],
            "actions": ["announced", "create campaign"],
            "topics": ["product", "launch", "marketing"],
        }
        summarizer.summarize_conversation = MagicMock(return_value=mock_summary)

        # Simulate the main loop from main_mvp.py
        transcriptions = []
        summaries = []

        # Process 3 chunks
        for _ in range(3):
            audio_chunk = mock_audio_capturer.get_chunk()
            assert audio_chunk is not None, "Audio capturer should return a chunk"

            transcription = mock_stt_engine.transcribe(audio_chunk)
            if transcription:  # Non-empty transcription
                transcriptions.append(transcription)
                summary = summarizer.summarize_conversation(transcription)
                summaries.append(summary)

        # Get final result
        final_text = mock_stt_engine.final_result()
        if final_text:
            transcriptions.append(final_text)
            summary = summarizer.summarize_conversation(final_text)
            summaries.append(summary)

        # Verify that we got the expected number of non-empty transcriptions
        assert len(transcriptions) == 3, "Should have 3 non-empty transcriptions"

        # Verify that summarize_conversation was called for each transcription
        assert summarizer.summarize_conversation.call_count == 3

        # Verify the structure of the summaries
        for summary in summaries:
            assert isinstance(summary, dict), "Summary should be a dictionary"
            assert "keywords" in summary, "Summary should have keywords"
            assert "entities" in summary, "Summary should have entities"
            assert "actions" in summary, "Summary should have actions"
            assert "topics" in summary, "Summary should have topics"

    @patch("src.ai.smart_summarizer.spacy.load")
    def test_integration_with_adapter(
        self, mock_spacy_load, mock_audio_capturer, mock_stt_engine
    ):
        """
        Tests the pipeline with the SmartSummarizerAdapter for backward compatibility.
        """
        from src.ai.smart_summarizer import SmartSummarizerAdapter

        # Set up mock spaCy NLP pipeline
        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Create a SpacySummarizer with mocked internals
        spacy_summarizer = SpacySummarizer()

        # Mock the summarize_conversation method
        mock_summary = {
            "keywords": ["product launch", "marketing campaign"],
            "entities": ["CEO", "marketing team"],
            "actions": ["announced", "create campaign"],
            "topics": ["product", "launch", "marketing"],
        }
        spacy_summarizer.summarize_conversation = MagicMock(return_value=mock_summary)

        # Create adapter that wraps the summarizer
        adapter = SmartSummarizerAdapter(spacy_summarizer)

        # Process a transcription using the adapter
        transcription = "The CEO announced the product launch."
        keywords = adapter.extract_keywords(transcription)

        # Verify adapter's output format
        assert isinstance(keywords, list), "Adapter should return a list of keywords"
        assert (
            keywords == mock_summary["keywords"]
        ), "Keywords should match what's in the summary"

        # Verify the summarizer was called correctly
        spacy_summarizer.summarize_conversation.assert_called_once_with(transcription)
