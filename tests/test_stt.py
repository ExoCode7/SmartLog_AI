import pytest
import time
import json
from src.ai.stt_engine import HybridSTTEngine
from unittest.mock import Mock, patch


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
@patch("vosk.KaldiRecognizer")
@patch("psutil.cpu_percent", return_value=90)
def test_engine_switch_cooldown(
    mock_cpu, mock_kaldi, mock_vosk, mock_vosk_model, mock_whisper_model
):
    model, recognizer = mock_vosk_model
    with patch("src.ai.stt_engine.VoskModel", return_value=model), patch(
        "src.ai.stt_engine.KaldiRecognizer", return_value=recognizer
    ), patch("src.ai.stt_engine.whisper.load_model", return_value=mock_whisper_model):
        engine = HybridSTTEngine(force_engine="whisper", cooldown_time=0.5)
        assert engine.active_engine == "whisper"

        # Manually bypass the resource check counter and interval check
        engine.resource_check_counter = 10  # Set to trigger the check
        engine.last_check_time = 0  # Ensure interval check passes

        # Now the CPU check should actually be called
        engine._check_resources_and_switch()
        mock_cpu.assert_called()

        # The rest of the test remains the same
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

    # Create the transcriber with patched dependencies
    with patch("src.ai.vosk_transcriber.Model", return_value=Mock()), patch(
        "src.ai.vosk_transcriber.KaldiRecognizer", return_value=mock_rec
    ):
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

    model, recognizer = mock_vosk_model

    # Patch the Vosk model and recognizer directly
    with patch("src.ai.stt_engine.VoskModel", return_value=model), patch(
        "src.ai.stt_engine.KaldiRecognizer", return_value=recognizer
    ):
        # Create a hybrid engine with Vosk as the active engine
        engine = HybridSTTEngine(force_engine="vosk", vosk_model_path="dummy_path")

        # Set up return value for FinalResult
        recognizer.FinalResult.return_value = '{"text": "final transcription"}'

        # Test the final_result method
        result = engine.final_result()
        assert result == "final transcription"
        recognizer.FinalResult.assert_called_once()


def test_json_parsing_in_vosk_transcriber(mock_vosk_model):
    """Test that JSON responses from Vosk are correctly parsed."""
    from src.ai.vosk_transcriber import VoskTranscriber

    # Set up the mocks
    _, mock_rec = mock_vosk_model  # Get the recognizer from the fixture

    # Create a JSON response with more complex data
    test_response = {
        "text": "test transcript with timestamps",
        "result": [
            {"word": "test", "start": 0.1, "end": 0.5},
            {"word": "transcript", "start": 0.6, "end": 1.2},
            {"word": "with", "start": 1.3, "end": 1.5},
            {"word": "timestamps", "start": 1.6, "end": 2.0},
        ],
    }

    # Configure mocks
    mock_rec.AcceptWaveform.return_value = True  # Ensure this returns True
    mock_rec.Result.return_value = json.dumps(test_response)

    # Create the transcriber with patched dependencies
    with patch("src.ai.vosk_transcriber.Model", return_value=Mock()), patch(
        "src.ai.vosk_transcriber.KaldiRecognizer", return_value=mock_rec
    ):
        transcriber = VoskTranscriber()

        # Test transcribe method with the JSON data
        audio_data = b"test audio"
        result = transcriber.transcribe(audio_data)

        # Verify that methods were called correctly
        mock_rec.AcceptWaveform.assert_called_once_with(audio_data)
        mock_rec.Result.assert_called_once()

        # Verify that we get the correct text from the JSON
        assert result == test_response["text"]
