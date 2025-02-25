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


@pytest.fixture
def mock_vosk_model():
    with patch("vosk.Model") as mock_class:
        mock_instance = mock_class.return_value
        mock_instance._handle = Mock(return_value=True)

        with patch("vosk.KaldiRecognizer") as mock_recognizer:
            recognizer_instance = mock_recognizer.return_value
            recognizer_instance.Result.return_value = '{"text": "test"}'
            recognizer_instance.PartialResult.return_value = '{"partial": "test"}'
            recognizer_instance.AcceptWaveform.return_value = True

            mock_class.side_effect = None
            yield mock_class
