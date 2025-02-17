import psutil
import time
import logging
from src.ai.stt_engine import HybridSTTEngine

logger = logging.getLogger(__name__)

class PowerAwareScheduler:
    def __init__(self, engine: HybridSTTEngine, temp_threshold: float = 85.0, check_interval: float = 5.0):
        self.engine = engine
        self.temp_threshold = temp_threshold
        self.check_interval = check_interval
        self.last_check_time = 0
        self.is_throttled = False

    def get_cpu_temp(self) -> float:
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            else:
                logger.warning("Could not determine CPU temperature.")
                return 0.0
        except Exception as e:
            logger.error(f"Error reading CPU temperature: {e}")
            return 0.0

    def throttle_check(self) -> bool:
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return False

        self.last_check_time = current_time
        temp = self.get_cpu_temp()
        if temp > self.temp_threshold:
            if not self.is_throttled:
                logger.warning(f"CPU temperature ({temp:.1f}°C) exceeds threshold ({self.temp_threshold}°C). Throttling...")
                self.is_throttled = True
                self._switch_to_low_power_mode()
                return True
        elif self.is_throttled:
            logger.info(f"CPU temperature ({temp:.1f}°C) below threshold. Resuming normal operation.")
            self.is_throttled = False
            self._switch_to_normal_mode()
            return False
        return False

    def _switch_to_low_power_mode(self):
        logger.info("Switching to low-power mode: forcing engine to Vosk.")
        # Force STT engine to Vosk
        self.engine.unload_whisper()
        self.engine.active_engine = "vosk"

    def _switch_to_normal_mode(self):
        logger.info("Switching to normal mode.")
        # Possibly allow the engine to switch back to whisper if usage is moderate 