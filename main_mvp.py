import sys
import traceback
from src.utils.logger import setup_logger
from src.gui.ui_tk import LiveTranscriptionUI
from src.audio.capture import AudioCapturer
from src.ai.stt_engine import HybridSTTEngine
from src.ai.summarization import KeywordEngine


def main():
    log = setup_logger()
    log.info("Starting SmartLog AI MVP (Phase 2/3)")

    audio = AudioCapturer()
    stt_engine = HybridSTTEngine()
    summarizer = KeywordEngine()

    def start_capture():
        audio.start()

    def stop_capture():
        audio.stop()

    ui = LiveTranscriptionUI(start_callback=start_capture, stop_callback=stop_capture)

    try:
        while True:
            audio_chunk = audio.get_chunk()
            if not audio_chunk:
                continue
            transcription = stt_engine.transcribe(audio_chunk)
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
        sys.exit(0)


if __name__ == "__main__":
    main()
