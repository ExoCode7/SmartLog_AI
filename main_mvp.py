import sys
import traceback
import logging
from src.utils.logger import setup_logger
from src.gui.ui_tk import LiveTranscriptionUI
from src.audio.capture import AudioCapturer
from src.ai.stt_engine import HybridSTTEngine
from src.ai.summarization import KeywordEngine


# Configure a fallback logger in case setup_logger fails
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


def main():
    try:
        # Set up logging with both file and console output
        log = setup_logger()
    except Exception as e:
        # Use the fallback logger if setup_logger fails
        log = logging.getLogger("fallback")
        log.error(f"Failed to initialize custom logger: {e}. Using fallback.")

    log.info("Starting SmartLog AI MVP (Phase 2/3)")

    # Updated model path from src/main_mvp.py
    MODEL_PATH = "models/vosk-model-small-en-us-0.15"
    SAMPLE_RATE = 16000

    # Initialize components
    audio = AudioCapturer(rate=SAMPLE_RATE, chunk=1600)
    stt_engine = HybridSTTEngine(vosk_model_path=MODEL_PATH)
    summarizer = KeywordEngine()

    def start_capture():
        log.info("Starting audio capture")
        audio.start()

    def stop_capture():
        log.info("Stopping audio capture")
        audio.stop()

    # Creating UI with added logging
    ui = LiveTranscriptionUI(start_callback=start_capture, stop_callback=stop_capture)

    # Add logging to UI methods by extending the LiveTranscriptionUI class
    original_on_start = ui.on_start
    original_on_stop = ui.on_stop
    original_update_display = ui.update_display

    def logged_on_start():
        log.info("UI: Start button clicked")
        original_on_start()

    def logged_on_stop():
        log.info("UI: Stop button clicked")
        original_on_stop()

    def logged_update_display(transcription, keywords):
        log.debug(
            f"UI: Updating display with transcription: '{transcription}' "
            f"and keywords: {keywords}"
        )
        original_update_display(transcription, keywords)

    ui.on_start = logged_on_start
    ui.on_stop = logged_on_stop
    ui.update_display = logged_update_display

    try:
        log.info("Starting transcription loop. Press Ctrl+C to stop.")
        while True:
            audio_chunk = audio.get_chunk()
            if not audio_chunk:
                continue

            transcription = stt_engine.transcribe(audio_chunk)
            if transcription:
                keywords = summarizer.extract_keywords(transcription)
                ui.update_display(transcription, keywords)

    except KeyboardInterrupt:
        log.info("Received KeyboardInterrupt, shutting down gracefully.")
    except Exception as e:
        log.error("Unhandled exception in main loop: %s", e)
        traceback.print_exc()
    finally:
        log.info("Stopping audio capture.")
        audio.stop()

        # Get any final transcription from the STT engine
        final_text = stt_engine.final_result()
        if final_text:
            log.info(f"Final transcription: {final_text}")
            keywords = summarizer.extract_keywords(final_text)
            ui.update_display(final_text, keywords)

        log.info("Exiting main_mvp.")
        sys.exit(0)


if __name__ == "__main__":
    main()
