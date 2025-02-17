import psutil
import time
import numpy as np
import logging
from vosk import Model as VoskModel, KaldiRecognizer
import whisper

try:
    from whisper_cpp_py import Whisper as WhisperCpp
    from whisper_cpp_py import WhisperCppParams
    WHISPER_CPP_AVAILABLE = True
except ImportError:
    WHISPER_CPP_AVAILABLE = False
    WhisperCpp = None
    WhisperCppParams = None

logger = logging.getLogger(__name__)

class HybridSTTEngine:
    def __init__(self, vosk_model_path="models/vosk-en-small",
                 whisper_model_name="tiny.en",
                 force_engine=None,
                 whisper_cpp_model_path="models/ggml-tiny.en-q4.bin",
                 temp_threshold=85.0,
                 check_interval=5.0,
                 cooldown_time=30.0):
        self.active_engine = "vosk" if not force_engine else force_engine
        self.vosk_model = VoskModel(vosk_model_path)
        self.vosk_recognizer = KaldiRecognizer(self.vosk_model, 16000)
        self.whisper_model = None
        self.whisper_cpp_model_path = whisper_cpp_model_path
        self.whisper_cpp_ctx = None
        self.temp_threshold = temp_threshold
        self.check_interval = check_interval
        self.cooldown_time = cooldown_time
        self.last_switch_time = 0
        self._load_whisper_if_forced()

    def _load_whisper_if_forced(self):
        if self.active_engine == "whisper":
            self._load_whisper()

    def _load_whisper(self):
        if self.whisper_model is None and WHISPER_CPP_AVAILABLE:
            try:
                logger.info(f"Loading whisper.cpp model: {self.whisper_cpp_model_path}")
                self.whisper_cpp_ctx = WhisperCpp.from_pretrained(self.whisper_cpp_model_path)
                logger.info("whisper.cpp model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load whisper.cpp model: {e}")
                raise
        elif self.whisper_model is None:
            self.whisper_model = whisper.load_model("tiny.en", device="cpu")

    def transcribe(self, audio_chunk: bytes) -> str:
        self._check_resources_and_switch()
        if self.active_engine == "vosk":
            if self.vosk_recognizer.AcceptWaveform(audio_chunk):
                result = self.vosk_recognizer.Result()
            else:
                result = self.vosk_recognizer.PartialResult()
            return result
        elif self.active_engine == "whisper":
            self._load_whisper()
            if self.whisper_cpp_ctx:
                params = WhisperCppParams()
                params.language = "en"
                params.n_threads = self._get_optimal_threads()
                audio_data_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                result = self.whisper_cpp_ctx.transcribe(audio_data_np, params)
                return result
            elif self.whisper_model:
                result_dict = self.whisper_model.transcribe(audio_chunk, fp16=False)
                return result_dict.get("text", "")
            else:
                logger.warning("No Whisper model loaded, returning empty string.")
                return ""
        else:
            logger.error("Unknown engine specified.")
            return ""

    def _check_resources_and_switch(self):
        current_time = time.time()
        if current_time - self.last_switch_time < self.cooldown_time:
            return  # avoid rapid switching

        # Check CPU usage, temperature, or memory usage
        cpu_percent = psutil.cpu_percent()
        virtual_mem = psutil.virtual_memory()
        if cpu_percent > 85 or virtual_mem.percent > 85:
            # Switch to vosk if we're not already on it
            if self.active_engine == "whisper":
                logger.info("High resource usage detected. Switching to Vosk.")
                self.unload_whisper()
                self.active_engine = "vosk"
                self.last_switch_time = current_time
        else:
            # If usage is moderate, we can switch to whisper if it was forced or user wants better accuracy
            # This is a simple example logic; you can refine further
            if self.active_engine == "vosk":
                # Optionally switch to whisper if we want better accuracy
                pass

    def _get_optimal_threads(self) -> int:
        return psutil.cpu_count(logical=False)

    def unload_whisper(self):
        if self.whisper_cpp_ctx is not None:
            del self.whisper_cpp_ctx
            self.whisper_cpp_ctx = None
            logger.info("Whisper.cpp model unloaded.")
        elif self.whisper_model is not None:
            # For original Whisper, there's no explicit unload, but you can drop references
            self.whisper_model = None
            logger.info("Original Whisper model reference dropped.")
