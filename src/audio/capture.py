import pyaudio
import threading
import logging
import time
from src.utils.buffer import RingBuffer

logger = logging.getLogger(__name__)

class AudioCapturer:
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1600  # ~100ms at 16kHz

    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.buffer = RingBuffer(10 * self.RATE)  # 10s buffer
        self._running = False
        self._capture_thread = None

    def start(self):
        logger.info("Starting audio capture.")
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=None
        )
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_audio, daemon=True)
        self._capture_thread.start()

    def _capture_audio(self):
        try:
            while self._running:
                in_data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                # Write to ring buffer
                try:
                    self.buffer.write(in_data)
                except Exception as e:
                    logger.error(f"Error writing to buffer: {e}")
        except (OSError, IOError) as e:
            logger.error(f"Audio capture error: {e}")
        except Exception as e:
            logger.exception("Unhandled exception in _capture_audio:", exc_info=e)
        logger.info("Exiting _capture_audio loop.")

    def get_chunk(self) -> bytes:
        """Retrieve one chunk (CHUNK bytes) from the ring buffer."""
        try:
            return self.buffer.read(self.CHUNK)
        except Exception as e:
            logger.error(f"Error reading from buffer: {e}")
            return b""

    def stop(self):
        logger.info("Stopping audio capture.")
        self._running = False
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        logger.info("Audio capture stopped.") 