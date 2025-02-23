import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_audio_capture():
    mock = Mock()
    with patch("src.audio.capture.AudioCapturer", return_value=mock) as mock_class:
        mock.get_chunk.return_value = b"test_audio"
        yield mock_class


@pytest.fixture
def mock_stt_engine():
    with patch("src.ai.stt_engine.HybridSTTEngine") as mock:
        mock.return_value.transcribe.return_value = "test transcription"
        yield mock


@pytest.fixture
def mock_vosk():
    with patch("src.ai.stt_engine.VoskModel") as mock:
        mock.return_value.Result.return_value = '{"text": "test"}'
        yield mock


@pytest.fixture
def mock_whisper():
    with patch("src.ai.stt_engine.WhisperModel") as mock:
        mock.return_value.transcribe.return_value = {"text": "test"}
        yield mock
