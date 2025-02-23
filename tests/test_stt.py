import pytest
import time
from src.ai.stt_engine import HybridSTTEngine
from unittest.mock import Mock, patch


@pytest.fixture
def mock_vosk_model(mocker):
    model = Mock()
    recognizer = Mock()
    model._handle = Mock()
    recognizer.Result.return_value = '{"text": "test"}'
    recognizer.PartialResult.return_value = '{"partial": "test"}'

    with patch("vosk.Model", return_value=model), patch(
        "vosk.KaldiRecognizer", return_value=recognizer
    ):
        yield model


@pytest.fixture
def mock_whisper_model():
    mock_model = Mock()
    mock_model.transcribe.return_value = {"text": "test"}
    with patch("whisper.load_model", return_value=mock_model):
        yield mock_model


def test_vosk_transcription(mock_vosk_model):
    engine = HybridSTTEngine(force_engine="vosk", vosk_model_path="dummy_path")
    result = engine.transcribe(b"fakeaudio")
    assert isinstance(result, str)
    assert "test" in result


def test_whisper_transcription_minimal(mock_whisper_model):
    engine = HybridSTTEngine(force_engine="whisper", whisper_model_name="tiny")
    result = engine.transcribe(b"fakeaudio")
    assert isinstance(result, str)
    assert "test" in result


@patch("psutil.cpu_percent", return_value=90)  # Simulate high CPU usage
def test_engine_switch_cooldown(mock_cpu, mock_vosk_model, mock_whisper_model):
    engine = HybridSTTEngine(force_engine="whisper", cooldown_time=0.5)
    assert engine.active_engine == "whisper"
    # Simulate high usage => switch to Vosk
    engine._check_resources_and_switch()
    assert engine.active_engine in ["whisper", "vosk"]
    time.sleep(1.0)  # wait beyond cooldown
    engine._check_resources_and_switch()
    mock_cpu.assert_called()
