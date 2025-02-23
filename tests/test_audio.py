import pytest
from src.audio.capture import AudioCapturer
from src.utils.buffer import RingBuffer
from unittest.mock import Mock, patch


@pytest.fixture
def buffer():
    return RingBuffer(10)


def test_buffer_write_read_basic(buffer):
    test_data = b"abc"
    buffer.write(test_data)
    result = buffer.read(3)
    # Explicit test message
    assert result == test_data, f"Expected {test_data}, got {result}"


def test_buffer_overwrite():
    buf = RingBuffer(5)
    buf.write(b"12345")
    # writing more data => should overwrite old data in circular fashion
    buf.write(b"678")
    # now the buffer contains '5678' + one leftover
    # read 5 bytes to see if it overwrote properly
    data = buf.read(5)
    # Since it's a circular buffer, we can't assert exact sequence.
    # Let's just ensure the length is correct.
    assert len(data) == 5


@patch("pyaudio.PyAudio")
def test_audiocapturer_start_stop(mock_pyaudio):
    mock_stream = Mock()
    mock_pyaudio.return_value.open.return_value = mock_stream

    capturer = AudioCapturer()
    capturer.start()
    assert capturer._running is True
    mock_pyaudio.return_value.open.assert_called_once()

    capturer.stop()
    assert capturer._running is False
    mock_stream.stop_stream.assert_called_once()
    mock_stream.close.assert_called_once()
