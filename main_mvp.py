import sys
import traceback
import logging
import os
from src.utils.logger import setup_logger
from src.gui.ui_tk import LiveTranscriptionUI
from src.audio.capture import AudioCapturer
from src.ai.stt_engine import HybridSTTEngine
from src.ai.summarization import KeywordEngine
from src.ai.smart_summarizer import SpacySummarizer, SmartSummarizerAdapter


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

    log.info("Starting SmartLog AI MVP (Phase 2.5 - Enhanced Summarization)")

    # Get model path from environment or use default
    MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")
    SAMPLE_RATE = 16000

    # Initialize components
    audio = AudioCapturer(rate=SAMPLE_RATE, chunk=1600)
    stt_engine = HybridSTTEngine(vosk_model_path=MODEL_PATH)

    # Initialize the new SpacySummarizer and use it with the adapter
    # for backward compatibility
    try:
        log.info("Initializing SpacySummarizer...")
        spacy_summarizer = SpacySummarizer(max_items_per_category=5)

        # For backward compatibility, wrap with adapter
        # Set use_adapter to False to use the full structured summary
        use_adapter = False

        if use_adapter:
            log.info("Using adapter for backward compatibility")
            summarizer = SmartSummarizerAdapter(spacy_summarizer)
        else:
            log.info("Using full structured summarizer")
            summarizer = spacy_summarizer
    except Exception as e:
        log.error(
            f"Failed to initialize SpacySummarizer: {e}. "
            f"Falling back to KeywordEngine."
        )
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

    def logged_update_display(transcription, summary):
        log.debug(
            f"UI: Updating display with transcription: '{transcription}' "
            f"and summary: {summary}"
        )
        original_update_display(transcription, summary)

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
                # Process with the summarizer - works with both adapter
                # and direct summarizer
                if isinstance(summarizer, SmartSummarizerAdapter):
                    keywords = summarizer.extract_keywords(transcription)
                    ui.update_display(transcription, keywords)
                else:
                    summary = summarizer.summarize_conversation(transcription)
                    ui.update_display(transcription, summary)

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
            # Process with the appropriate summarizer
            if isinstance(summarizer, SmartSummarizerAdapter):
                keywords = summarizer.extract_keywords(final_text)
                ui.update_display(final_text, keywords)
            else:
                summary = summarizer.summarize_conversation(final_text)
                ui.update_display(final_text, summary)

        log.info("Exiting main_mvp.")
        sys.exit(0)


if __name__ == "__main__":
    main()
