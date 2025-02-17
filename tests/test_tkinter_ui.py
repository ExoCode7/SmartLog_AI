import pytest
import tkinter
from src.gui.ui_tk import LiveTranscriptionUI

def test_ui_creation():
    ui = LiveTranscriptionUI()
    assert isinstance(ui, LiveTranscriptionUI)

def test_ui_update_display():
    ui = LiveTranscriptionUI()
    ui.update_display("Hello world", ["hello", "world"])
    assert True

def test_ui_concurrency():
    # We won't call ui.run() but we simulate multiple updates
    ui = LiveTranscriptionUI()
    for i in range(5):
        ui.update_display(f"Line {i}", [f"keyword{i}"])
    assert True 