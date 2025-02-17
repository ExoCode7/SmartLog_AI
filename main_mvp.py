import logging
from src.utils.logger import setup_logger
from src.gui.ui_tk import MinimalUI


def main():
    log = setup_logger()
    log.info("Starting SmartLog AI MVP Phase 1")

    # Initialize and run minimal UI
    app = MinimalUI()
    app.run()


if __name__ == "__main__":
    main()
