import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

def get_logger(submodule_name: str) -> logging.Logger:
    """
    Returns a logger that writes logs to a file named after the submodule and current date.
    Log files are stored in a 'logs' directory.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"{submodule_name}_{date_str}.log"
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger(submodule_name)
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers if get_logger is called multiple times
    if not logger.handlers:
        handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=5)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


    return logger