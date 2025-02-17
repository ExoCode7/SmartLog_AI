import pyaudio
import logging
import threading
import queue
import vosk
import json


class AudioCapture:
    def __init__(
        self, device_index=None, sample_rate=16000, chunk_size=1024, buffer_size=4
    ):
        """
        Captures audio in a separate thread, storing chunks in a queue.
        device_index: Optional index of audio input device (None = default).
        sample_rate: Must match your Vosk model if you want accurate transcription.
        chunk_size: Number of frames per read.
        buffer_size: Number of chunks to queue.
        """
        self.logger = logging.getLogger(__name__)
        self.p = pyaudio.PyAudio()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.stream = None
        self.frames = queue.Queue(maxsize=buffer_size)  # Thread-safe queue
        self.running = False
        self.capture_thread = None
        self.lock = threading.Lock()

    def _capture_audio(self):
        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
            )
            self.logger.info("Audio capture started.")
            while self.running:
                with self.lock:
                    data = self.stream.read(
                        self.chunk_size, exception_on_overflow=False
                    )
                self.frames.put(data)
        except Exception as e:
            self.logger.error(f"Error during audio capture: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.logger.info("Audio capture stopped.")

    def start_capture(self):
        """Starts capturing audio in a daemon thread."""
        if not self.running:
            self.running = True
            self.capture_thread = threading.Thread(
                target=self._capture_audio, daemon=True
            )
            self.capture_thread.start()
        else:
            self.logger.warning("Audio capture already running.")

    def stop_capture(self):
        """Stops the capture process and joins the thread."""
        if self.running:
            with self.lock:
                self.running = False
            if self.capture_thread:
                self.capture_thread.join()
            self.logger.info("Audio capture thread joined.")
        else:
            self.logger.warning("Audio capture not running.")

    def get_audio_data(self):
        """Retrieves one chunk of audio data (non-blocking). Returns None if queue is empty."""
        try:
            return self.frames.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        """Stops capture if running and terminates PyAudio."""
        with self.lock:
            self.stop_capture()
            self.p.terminate()
            self.logger.info("PyAudio terminated.")


class VoskTranscriber:
    def __init__(self, model_path="model", sample_rate=16000):
        """
        model_path: Path to the Vosk model folder.
        sample_rate: Must match your audio capture rate for accurate recognition.
        """
        self.logger = logging.getLogger(__name__)
        self.sample_rate = sample_rate
        try:
            self.model = vosk.Model(model_path)
            self.rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.rec.SetWords(True)  # More detailed results
        except Exception as e:
            self.logger.error(f"Error initializing Vosk: {e}")
            raise

    def transcribe(self, audio_data):
        """Feeds audio_data to the recognizer. Returns full text if a segment is done, else partial text."""
        try:
            if self.rec.AcceptWaveform(audio_data):
                result = self.rec.Result()
                result_dict = json.loads(result)
                return result_dict.get("text", "")
            else:
                partial = self.rec.PartialResult()
                partial_dict = json.loads(partial)
                return partial_dict.get("partial", "")
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")
            return ""

    def final_result(self):
        """Fetches any leftover recognized text after capture stops."""
        try:
            result = self.rec.FinalResult()
            result_dict = json.loads(result)
            return result_dict.get("text", "")
        except Exception as e:
            self.logger.error(f"Error getting final result: {e}")
            return ""
