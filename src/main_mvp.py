import logging
import logging.config
import time
from audio import AudioCapture, VoskTranscriber

def setup_logging(default_path='logging.ini', default_level=logging.INFO):
    try:
        with open(default_path, 'rt') as f:
            logging.config.fileConfig(f, disable_existing_loggers=False)
    except Exception as e:
        print(f"Error in Logging Configuration. Using default configs: {e}")
        logging.basicConfig(level=default_level)

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    MODEL_PATH = "model"  # Adjust if needed
    SAMPLE_RATE = 16000   # Must match your Vosk model

    audio_capture = None
    try:
        audio_capture = AudioCapture(sample_rate=SAMPLE_RATE)
        transcriber = VoskTranscriber(model_path=MODEL_PATH, sample_rate=SAMPLE_RATE)

        audio_capture.start_capture()
        logger.info("Starting transcription loop. Press Ctrl+C to stop.")

        while True:
            data = audio_capture.get_audio_data()
            if data:
                text = transcriber.transcribe(data)
                if text:
                    print(f"Transcription: {text}")
            time.sleep(0.01)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, stopping.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
    finally:
        if audio_capture:
            audio_capture.close()
        logger.info("Exiting main_mvp.")

if __name__ == "__main__":
    main() 