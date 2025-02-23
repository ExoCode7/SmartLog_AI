import pytest
import tkinter
from src.gui.ui_tk import LiveTranscriptionUI
from unittest.mock import Mock, patch


@patch("tkinter.Tk")
@patch("tkinter.scrolledtext.ScrolledText")
def test_ui_creation(mock_text, mock_tk):
    mock_text.return_value = Mock()
    ui = LiveTranscriptionUI()
    assert isinstance(ui, LiveTranscriptionUI)
    mock_tk.assert_called_once()
    mock_text.assert_called_once()


@pytest.fixture
def mock_tk():
    with patch("tkinter.Tk") as mock_tk, patch(
        "tkinter.scrolledtext.ScrolledText"
    ) as mock_text:
        mock_text.return_value.get.return_value = "Hello world"
        mock_text.return_value = Mock()
        yield mock_tk


def test_ui_update_display(mock_tk):
    ui = LiveTranscriptionUI()
    test_text = "Hello world"
    test_keywords = ["hello", "world"]
    ui.update_display(test_text, test_keywords)
    ui.text_area.insert.assert_called_with(tkinter.END, test_text + "\n")


@patch("threading.Thread")
def test_ui_concurrency(mock_thread):
    ui = LiveTranscriptionUI()
    for i in range(5):
        ui.update_display(f"Line {i}", [f"keyword{i}"])
    mock_thread.assert_not_called()  # Ensure we're not actually creating threads
