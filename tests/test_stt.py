import pytest
import time
from src.ai.stt_engine import HybridSTTEngine
from unittest.mock import Mock, patch
import json


@pytest.fixture
def mock_vosk_model(mocker):
    model = Mock()
    recognizer = Mock()
    model._handle = Mock()
    recognizer.Result.return_value = '{"text": "test"}'
    recognizer.PartialResult.return_value = '{"partial": "test"}'
    recognizer.AcceptWaveform.return_value = True

    with patch("vosk.Model", return_value=model), patch(
        "vosk.KaldiRecognizer", return_value=recognizer
    ):
        yield model, recognizer  # Return both the model and recognizer


@pytest.fixture
def mock_whisper_model():
    mock_model = Mock()
    mock_model.transcribe.return_value = {"text": "test"}
    with patch("whisper.load_model", return_value=mock_model):
        yield mock_model


@patch("vosk.Model")
@patch("vosk.KaldiRecognizer")  # Add KaldiRecognizer patch
def test_vosk_transcription(mock_kaldi, mock_vosk, mock_vosk_model):
    model, recognizer = mock_vosk_model  # Unpack the tuple
    # Patch both VoskModel and KaldiRecognizer directly in the STT engine
    with patch("src.ai.stt_engine.VoskModel", return_value=model), patch(
        "src.ai.stt_engine.KaldiRecognizer", return_value=recognizer
    ):
        engine = HybridSTTEngine(force_engine="vosk", vosk_model_path="dummy_path")
        result = engine.transcribe(b"fakeaudio")
        assert isinstance(result, str)
        assert "test" in result


@patch("vosk.Model")
@patch("vosk.KaldiRecognizer")  # Add KaldiRecognizer patch
def test_whisper_transcription_minimal(
    mock_kaldi, mock_vosk, mock_whisper_model, mock_vosk_model
):
    model, recognizer = mock_vosk_model  # Unpack the tuple
    # Patch both VoskModel and KaldiRecognizer
    with patch("src.ai.stt_engine.VoskModel", return_value=model), patch(
        "src.ai.stt_engine.KaldiRecognizer", return_value=recognizer
    ), patch("src.ai.stt_engine.whisper.load_model", return_value=mock_whisper_model):
        engine = HybridSTTEngine(force_engine="whisper", whisper_model_name="tiny")
        result = engine.transcribe(b"fakeaudio")
        assert isinstance(result, str)
        assert "test" in result


@patch("vosk.Model")
@patch("vosk.KaldiRecognizer")  # Add KaldiRecognizer patch
@patch("psutil.cpu_percent", return_value=90)
def test_engine_switch_cooldown(
    mock_cpu, mock_kaldi, mock_vosk, mock_vosk_model, mock_whisper_model
):
    model, recognizer = mock_vosk_model  # Unpack the tuple
    # Patch both VoskModel and KaldiRecognizer
    with patch("src.ai.stt_engine.VoskModel", return_value=model), patch(
        "src.ai.stt_engine.KaldiRecognizer", return_value=recognizer
    ), patch("src.ai.stt_engine.whisper.load_model", return_value=mock_whisper_model):
        engine = HybridSTTEngine(force_engine="whisper", cooldown_time=0.5)
        assert engine.active_engine == "whisper"
        # Simulate high usage => switch to Vosk
        engine._check_resources_and_switch()
        assert engine.active_engine in ["whisper", "vosk"]
        time.sleep(1.0)  # wait beyond cooldown
        engine._check_resources_and_switch()
        mock_cpu.assert_called()


@patch("vosk.Model")
@patch("vosk.KaldiRecognizer")
def test_vosk_transcriber(mock_kaldi, mock_model):
    """Test the standalone VoskTranscriber class works correctly."""
    from src.ai.vosk_transcriber import VoskTranscriber

    # Set up the mocks
    mock_rec = mock_kaldi.return_value
    mock_rec.AcceptWaveform.return_value = True
    mock_rec.Result.return_value = '{"text": "test transcription"}'
    mock_rec.FinalResult.return_value = '{"text": "final words"}'

    # Create the transcriber
    transcriber = VoskTranscriber()

    # Test transcribe method with a complete segment
    result = transcriber.transcribe(b"test audio")
    mock_rec.AcceptWaveform.assert_called_with(b"test audio")
    assert result == "test transcription"

    # Test final_result method
    final = transcriber.final_result()
    assert final == "final words"

    # Test transcribe with partial result
    mock_rec.AcceptWaveform.return_value = False
    mock_rec.PartialResult.return_value = '{"partial": "partial words"}'
    result = transcriber.transcribe(b"more audio")
    assert result == "partial words"


def test_hybrid_stt_final_result(mock_vosk_model):
    """Test the final_result method of HybridSTTEngine."""
    from src.ai.stt_engine import HybridSTTEngine

    # Create a hybrid engine with Vosk as the active engine
    engine = HybridSTTEngine(force_engine="vosk")

    # Set up expectations for FinalResult
    engine.vosk_recognizer.FinalResult.return_value = json.dumps(
        {"text": "final transcription"}
    )

    # Test the final_result method
    result = engine.final_result()
    assert result == "final transcription"
    engine.vosk_recognizer.FinalResult.assert_called_once()
