import logging


class SensitiveDataFilter(logging.Filter):
    """
    Filters out potentially sensitive information from log messages.
    """

    def filter(self, record):
        # Redact messages containing sensitive keywords
        sensitive_keywords = ["transcription:", "audio chunk:", "keywords:"]
        message = record.getMessage().lower()
        if any(keyword in message for keyword in sensitive_keywords):
            record.msg = "REDACTED: Sensitive data omitted."
            record.args = ()
        return True


def setup_logger():
    logger = logging.getLogger()  # Root logger
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler("smartlog_ai.log")
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Add sensitive data filter
    logger.addFilter(SensitiveDataFilter())
    return logger


if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Logger initialized with sensitive data filtering.")
