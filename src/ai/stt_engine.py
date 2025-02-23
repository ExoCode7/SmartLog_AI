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
    def __init__(
        self,
        vosk_model_path="models/vosk-en-small",
        whisper_model_name="tiny.en",
        force_engine=None,
        whisper_cpp_model_path="models/ggml-tiny.en-q4.bin",
        temp_threshold=85.0,
        check_interval=5.0,
        cooldown_time=30.0,
    ):
        self.active_engine = "vosk" if not force_engine else force_engine
        logger.info(
            "Initializing HybridSTTEngine with " f"active_engine={self.active_engine}"
        )

        self.vosk_model = VoskModel(vosk_model_path)
        self.vosk_recognizer = KaldiRecognizer(self.vosk_model, 16000)
        logger.info("Vosk model loaded successfully.")

        self.whisper_model = None
        self.whisper_cpp_model_path = whisper_cpp_model_path
        self.whisper_cpp_ctx = None
        self.whisper_model_name = whisper_model_name

        self.temp_threshold = temp_threshold
        self.check_interval = check_interval
        self.cooldown_time = cooldown_time
        self.last_switch_time = 0

        self._load_whisper_if_forced()

    def _load_whisper_if_forced(self):
        if self.active_engine == "whisper":
            logger.info(
                "Force-engine is set to whisper, " "attempting to load Whisper now."
            )
            self._load_whisper()

    def _load_whisper(self):
        if self.whisper_model is None and WHISPER_CPP_AVAILABLE:
            try:
                logger.info(
                    "Loading whisper.cpp model from path: "
                    f"{self.whisper_cpp_model_path}"
                )
                self.whisper_cpp_ctx = WhisperCpp.from_pretrained(
                    self.whisper_cpp_model_path
                )
                logger.info("whisper.cpp model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load whisper.cpp model: {e}")
                raise
        elif self.whisper_model is None:
            logger.info(
                "whisper.cpp not available, loading original "
                f"Whisper model: {self.whisper_model_name}"
            )
            self.whisper_model = whisper.load_model(
                self.whisper_model_name, device="cpu"
            )
            logger.info("Original Whisper model loaded successfully.")

    def transcribe(self, audio_chunk: bytes) -> str:
        self._check_resources_and_switch()
        if self.active_engine == "vosk":
            if self.vosk_recognizer.AcceptWaveform(audio_chunk):
                result = self.vosk_recognizer.Result()
                logger.debug(f"Vosk final result: {result}")
            else:
                result = self.vosk_recognizer.PartialResult()
                logger.debug(f"Vosk partial result: {result}")
            return result
        elif self.active_engine == "whisper":
            self._load_whisper()
            if self.whisper_cpp_ctx:
                params = WhisperCppParams()
                params.language = "en"
                params.n_threads = self._get_optimal_threads()
                audio_data_np = (
                    np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
                    / 32768.0
                )
                logger.debug("Transcribing with whisper.cpp context.")
                result = self.whisper_cpp_ctx.transcribe(audio_data_np, params)
                logger.debug(f"whisper.cpp result: {result}")
                return result
            elif self.whisper_model:
                logger.debug("Transcribing with original Whisper model.")
                result_dict = self.whisper_model.transcribe(audio_chunk, fp16=False)
                text = result_dict.get("text", "")
                logger.debug(f"Original Whisper result: {text}")
                return text
            else:
                logger.warning("No Whisper model loaded, returning empty string.")
                return ""
        else:
            logger.error(f"Unknown engine specified: {self.active_engine}")
            return ""

    def _check_resources_and_switch(self):
        current_time = time.time()
        if current_time - self.last_switch_time < self.cooldown_time:
            return

        cpu_percent = psutil.cpu_percent()
        virtual_mem = psutil.virtual_memory()

        # Use the variables for resource monitoring
        if cpu_percent > 80 or virtual_mem.percent > 90:
            logger.warning(
                "High resource usage: "
                f"CPU {cpu_percent}%, "
                f"Memory {virtual_mem.percent}%"
            )
            if self.active_engine == "whisper":
                self.active_engine = "vosk"
                self.unload_whisper()

    def _get_optimal_threads(self) -> int:
        return psutil.cpu_count(logical=False)

    def unload_whisper(self):
        if self.whisper_cpp_ctx is not None:
            del self.whisper_cpp_ctx
            self.whisper_cpp_ctx = None
            logger.info("whisper.cpp model unloaded.")
        elif self.whisper_model is not None:
            self.whisper_model = None
            logger.info("Original Whisper model reference dropped.")
