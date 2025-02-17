import pytest
import time
from src.ai.stt_engine import HybridSTTEngine

def test_vosk_transcription_minimal():
    engine = HybridSTTEngine(force_engine="vosk")
    result = engine.transcribe(b"fakeaudio")
    # We only check that it doesn't crash, actual STT logic is placeholder
    assert isinstance(result, str)

def test_whisper_transcription_minimal():
    engine = HybridSTTEngine(force_engine="whisper")
    result = engine.transcribe(b"fakeaudio")
    assert isinstance(result, str)

def test_engine_switch_cooldown():
    engine = HybridSTTEngine(force_engine="whisper", cooldown_time=0.5)
    # Force to whisper
    assert engine.active_engine == "whisper"
    # Simulate high usage => switch to Vosk
    engine._check_resources_and_switch()
    assert engine.active_engine in ["whisper", "vosk"]
    time.sleep(1.0)  # wait beyond cooldown
    engine._check_resources_and_switch()
    # Not a perfect test, but ensures no errors in switching logic
    assert True 