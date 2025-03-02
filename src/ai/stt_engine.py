import psutil
import time
import numpy as np
import logging
import json
import gc
import whisper
from typing import Optional, Dict

# Set up logger before using it
logger = logging.getLogger(__name__)

# Try to import whisper.cpp with graceful fallback
try:
    from vosk import Model as VoskModel, KaldiRecognizer
    from whisper_cpp import Context as WhisperCppContext
    from whisper_cpp.whisper_cpp import Params as WhisperCppParams

    WHISPER_CPP_AVAILABLE = True
except ImportError:
    logger.info("whisper.cpp not available, falling back to original Whisper")
    WHISPER_CPP_AVAILABLE = False

    # Create mock classes for type checking and tests
    class WhisperCppContext:
        def __init__(self, *args, **kwargs):
            pass

    class WhisperCppParams:
        def __init__(self):
            self.language = "en"
            self.n_threads = 4


class HybridSTTEngine:
    def __init__(
        self,
        vosk_model_path: str = "models/vosk-model-small-en-us-0.15",
        whisper_model_name: str = "tiny",
        whisper_cpp_model_path: Optional[str] = None,
        force_engine: Optional[str] = None,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 70.0,
        check_interval: float = 5.0,
        cooldown_time: float = 30.0,
    ):
        """
        A hybrid STT engine that can switch between Vosk and Whisper based on
        system resources.

        Args:
            vosk_model_path: Path to the Vosk model
            whisper_model_name: Name of the Whisper model to use
            whisper_cpp_model_path: Path to whisper.cpp model file
            force_engine: Force using a specific engine ("vosk" or "whisper")
            cpu_threshold: CPU usage percentage threshold for switching
            memory_threshold: Memory usage percentage threshold for switching
            check_interval: How often to check resource usage (seconds)
            cooldown_time: Time to wait between engine switches (seconds)
        """
        self.vosk_model_path = vosk_model_path
        self.whisper_model_name = whisper_model_name
        self.whisper_cpp_model_path = whisper_cpp_model_path

        # Resource management settings
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.check_interval = check_interval
        self.cooldown_time = cooldown_time

        # State tracking
        self.last_check_time = 0
        self.last_switch_time = 0
        self.resource_check_counter = 0  # Only check every N calls

        # Initialize engines
        self.vosk_model = None
        self.vosk_recognizer = None
        self.whisper_model = None
        self.whisper_cpp_ctx = None

        # Set active engine
        if force_engine and force_engine in ["vosk", "whisper"]:
            self.active_engine = force_engine
        else:
            # Start with Vosk as it's lighter on resources
            self.active_engine = "vosk"

        # Initialize the current active engine
        self._initialize_current_engine()

    def _initialize_current_engine(self):
        """Initialize only the currently active engine to save resources"""
        if self.active_engine == "vosk" and not self.vosk_recognizer:
            self._load_vosk()
        elif (
            self.active_engine == "whisper"
            and not self.whisper_model
            and not self.whisper_cpp_ctx
        ):
            self._load_whisper()

    def _load_vosk(self):
        """Load Vosk model and recognizer"""
        try:
            logger.info(f"Loading Vosk model from {self.vosk_model_path}")
            self.vosk_model = VoskModel(self.vosk_model_path)
            self.vosk_recognizer = KaldiRecognizer(self.vosk_model, 16000)
            self.vosk_recognizer.SetWords(True)
            logger.info("Vosk model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            raise

    def _load_whisper(self):
        """Load Whisper model (whisper.cpp if available, otherwise original Whisper)"""
        # Try whisper.cpp first if a model path is provided
        if WHISPER_CPP_AVAILABLE and self.whisper_cpp_model_path:
            try:
                if not self.whisper_cpp_ctx:
                    logger.info(
                        f"Loading whisper.cpp model from {self.whisper_cpp_model_path}"
                    )
                    self.whisper_cpp_ctx = WhisperCppContext(
                        self.whisper_cpp_model_path
                    )
                    logger.info("whisper.cpp model loaded successfully")
                return
            except Exception as e:
                logger.error(f"Failed to load whisper.cpp model: {e}")
                # Fall back to original Whisper

        # Load original Whisper if no whisper.cpp or it failed
        if not self.whisper_model:
            try:
                logger.info(f"Loading Whisper model: {self.whisper_model_name}")
                # Use device="cpu" to avoid GPU memory issues
                self.whisper_model = whisper.load_model(
                    self.whisper_model_name, device="cpu"
                )
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise

    def _get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        return {"cpu": cpu_percent, "memory": memory_percent}

    def _get_optimal_threads(self) -> int:
        """Determine optimal number of threads based on current system load"""
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent()

        if cpu_percent > 90:
            return max(1, cpu_count // 4)  # Use 25% of cores when very busy
        elif cpu_percent > 70:
            return max(1, cpu_count // 2)  # Use 50% of cores when moderately busy
        else:
            return max(1, int(cpu_count * 0.75))  # Use 75% of cores when not busy

    def _should_check_resources(self) -> bool:
        """Determine if resources should be checked based on time and counter"""
        self.resource_check_counter += 1

        # Only check every 10 calls to reduce overhead
        if self.resource_check_counter < 10:
            return False

        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return False

        self.last_check_time = current_time
        self.resource_check_counter = 0
        return True

    def _check_resources_and_switch(self):
        """Check system resources and switch engines if necessary"""
        # Skip check if not needed
        if not self._should_check_resources():
            return

        # Skip if in cooldown period
        current_time = time.time()
        if current_time - self.last_switch_time < self.cooldown_time:
            return

        # Get resource usage
        resources = self._get_system_resources()
        cpu_usage = resources["cpu"]
        memory_usage = resources["memory"]

        # Log high resource usage
        if cpu_usage > self.cpu_threshold or memory_usage > self.memory_threshold:
            logger.warning(
                f"High resource usage: CPU {cpu_usage}%, Memory {memory_usage}%"
            )

        # Determine if we need to switch engines
        current_engine = self.active_engine

        if current_engine == "whisper" and (
            cpu_usage > self.cpu_threshold or memory_usage > self.memory_threshold
        ):
            # Switch to Vosk if resources are high
            logger.info(
                f"Switching to Vosk due to high resource usage: "
                f"CPU {cpu_usage}%, Memory {memory_usage}%"
            )
            self.active_engine = "vosk"
            self._load_vosk()

            # Clean up Whisper to free memory
            self._unload_whisper()
            self.last_switch_time = current_time

        elif current_engine == "vosk" and (
            cpu_usage < self.cpu_threshold - 15
            and memory_usage < self.memory_threshold - 15
        ):
            # Switch to Whisper if resources are low (with hysteresis)
            logger.info(
                f"Switching to Whisper due to available resources: "
                f"CPU {cpu_usage}%, Memory {memory_usage}%"
            )
            self.active_engine = "whisper"
            self._load_whisper()
            self.last_switch_time = current_time

    def _unload_whisper(self):
        """Properly unload Whisper models to free memory"""
        if self.whisper_model:
            logger.info("Original Whisper model reference dropped.")
            self.whisper_model = None

        if self.whisper_cpp_ctx:
            logger.info("whisper.cpp context destroyed.")
            self.whisper_cpp_ctx = None

        # Force garbage collection to reclaim memory
        gc.collect()

    def transcribe(self, audio_chunk: bytes) -> str:
        """
        Transcribe audio chunk using the active engine.

        Args:
            audio_chunk: Raw audio data (16-bit PCM)

        Returns:
            Transcribed text
        """
        # Check resources and potentially switch engines
        self._check_resources_and_switch()

        # Process with the active engine
        if self.active_engine == "vosk":
            try:
                if not self.vosk_recognizer:
                    self._load_vosk()

                if self.vosk_recognizer.AcceptWaveform(audio_chunk):
                    result = self.vosk_recognizer.Result()
                    result_dict = json.loads(result)
                    return result_dict.get("text", "")
                else:
                    partial = self.vosk_recognizer.PartialResult()
                    partial_dict = json.loads(partial)
                    return partial_dict.get("partial", "")
            except Exception as e:
                logger.error(f"Error in Vosk transcription: {e}")
                return ""

        elif self.active_engine == "whisper":
            try:
                self._load_whisper()

                if self.whisper_cpp_ctx:
                    # Use whisper.cpp if available
                    params = WhisperCppParams()
                    params.language = "en"
                    params.n_threads = self._get_optimal_threads()

                    # Convert audio data to float32 format
                    audio_data_np = (
                        np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
                        / 32768.0
                    )

                    result = self.whisper_cpp_ctx.transcribe(audio_data_np, params)
                    return result

                elif self.whisper_model:
                    # Use original Whisper
                    result_dict = self.whisper_model.transcribe(audio_chunk, fp16=False)
                    return result_dict.get("text", "")
                else:
                    logger.warning("No Whisper model loaded, returning empty string.")
                    return ""
            except Exception as e:
                logger.error(f"Error in Whisper transcription: {e}")
                return ""
        else:
            logger.error(f"Unknown engine specified: {self.active_engine}")
            return ""

    def final_result(self) -> str:
        """Get final transcription result when done processing"""
        if self.active_engine == "vosk" and self.vosk_recognizer:
            try:
                result = self.vosk_recognizer.FinalResult()
                result_dict = json.loads(result)
                return result_dict.get("text", "")
            except Exception as e:
                logger.error(f"Error getting final result from Vosk: {e}")
                return ""
        return ""

    def close(self):
        """Release all resources"""
        self._unload_whisper()
        self.vosk_model = None
        self.vosk_recognizer = None
        gc.collect()
