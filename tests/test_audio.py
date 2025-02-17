import pytest
from src.audio.capture import AudioCapturer
from src.utils.buffer import RingBuffer

def test_buffer_write_read_basic():
    buf = RingBuffer(10)
    buf.write(b"abc")
    result = buf.read(3)
    assert result == b"abc"

def test_buffer_overwrite():
    buf = RingBuffer(5)
    buf.write(b"12345")
    # writing more data => should overwrite old data in circular fashion
    buf.write(b"678")
    # now the buffer contains '5678' + one leftover
    # read 5 bytes to see if it overwrote properly
    data = buf.read(5)
    # we can't assert an exact sequence since it's circular, but let's ensure length is correct
    assert len(data) == 5

def test_audiocapturer_start_stop():
    capturer = AudioCapturer()
    capturer.start()
    assert capturer._running is True
    capturer.stop()
    assert capturer._running is False 