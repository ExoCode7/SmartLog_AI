import logging
import json
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)


class VoskTranscriber:
    def __init__(
        self, model_path="models/vosk-model-small-en-us-0.15", sample_rate=16000
    ):
        """
        A simple transcriber using Vosk for speech recognition.

        Args:
            model_path: Path to the Vosk model folder.
            sample_rate: Must match your audio capture rate for accurate recognition.
        """
        self.logger = logger
        self.sample_rate = sample_rate
        try:
            self.model = Model(model_path)
            self.rec = KaldiRecognizer(self.model, self.sample_rate)
            self.rec.SetWords(True)  # More detailed results
        except Exception as e:
            self.logger.error(f"Error initializing Vosk: {e}")
            raise

    def transcribe(self, audio_data):
        """Feeds audio_data to the recognizer.
        Returns full text if a segment is done, else partial text."""
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
