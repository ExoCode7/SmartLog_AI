import pyaudio
import threading
import logging
import time  # noqa: F401
from src.utils.buffer import RingBuffer

logger = logging.getLogger(__name__)


class AudioCapturer:
    def __init__(
        self, rate=16000, chunk=1600, channels=1, buffer_duration=10, device_index=None
    ):
        """Initializes the AudioCapturer with configurable parameters.

        Args:
            rate: Sampling rate in Hz. Default is 16000.
            chunk: Frames per buffer. Default is 1600 (~100ms).
            channels: Number of audio channels. Default is 1.
            buffer_duration: Duration in seconds for ring buffer. Default is 10.
            device_index: Optional index of audio input device (None = default).
        """
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.buffer_size = buffer_duration * self.rate
        self.device_index = device_index
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.buffer = RingBuffer(self.buffer_size)
        self._running = False
        self._capture_thread = None

    def start(self) -> None:
        logger.info("Starting audio capture.")
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk,
            stream_callback=None,
        )
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_audio, daemon=True)
        self._capture_thread.start()

    def _capture_audio(self):
        try:
            while self._running:
                in_data = self.stream.read(self.chunk, exception_on_overflow=False)
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
        """
        Retrieve one chunk (self.chunk bytes) from the ring buffer.
        Returns an empty bytes object if none is available.
        """
        try:
            data = self.buffer.read(self.chunk)
            return data
        except Exception as e:
            logger.error(f"Error reading from buffer: {e}")
            return b""

    def stop(self):
        logger.info("Stopping audio capture.")
        self._running = False
        if self._capture_thread and self._capture_thread.is_alive():
            start_time = time.time()
            self._capture_thread.join(timeout=2.0)
            if time.time() - start_time >= 2.0:
                logger.warning("Thread join timed out")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        logger.info("Audio capture stopped.")

    # Compatibility method for old AudioCapture class
    def start_capture(self):
        """Compatibility method for AudioCapture.start_capture()"""
        return self.start()

    # Compatibility method for old AudioCapture class
    def get_audio_data(self):
        """Compatibility method for AudioCapture.get_audio_data()"""
        return self.get_chunk()

    # Compatibility method for old AudioCapture class
    def stop_capture(self):
        """Compatibility method for AudioCapture.stop_capture()"""
        return self.stop()

    # Compatibility method for old AudioCapture class
    def close(self):
        """Compatibility method for AudioCapture.close()"""
        return self.stop()
