# Module Imports
import logging
import logging.handlers

from constants import Constants

# Define ANSI escape sequences for colors
LOG_COLORS = {
    logging.DEBUG: "\033[94m",    # Blue
    logging.INFO: "\033[92m",     # Green
    logging.WARNING: "\033[93m",  # Yellow
    logging.ERROR: "\033[91m",    # Red
    logging.CRITICAL: "\033[31m", # Maroon
}

RESET_COLOR = "\033[0m"

# Custom Formatter to colorize [levelname]
class ColorFormatter(logging.Formatter):
    def format(self, record):
        # Get color from dictionary
        log_color: str = LOG_COLORS.get(record.levelno, RESET_COLOR)

        # Apply and return formatting
        record.levelname = f"{log_color}[{record.levelname}]{RESET_COLOR}"
        return super().format(record)

# Function to assign log level and format to a specified logger
def setup_logger(logger: logging.Logger, log_level: str) -> None:
    # Set log level, reset handlers
    logger.setLevel(getattr(logging, log_level))
    logger.handlers = []
    handler: logging.StreamHandler = logging.StreamHandler()

    # Apply formatting to handler
    handler_format = ColorFormatter(
        fmt='\033[90m{asctime} \033[34m{levelname} \x1b[38;5;98m[{name}]\033[97m: {message}\033[0m',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{'
    )
    handler.setFormatter(handler_format)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
