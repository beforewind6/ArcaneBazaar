import logging
import os

def setup_logger(name: str, log_file: str = "logs/app.log") -> logging.Logger:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(name)s - %(asctime)s - %(levelname)s - %(message)s"
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger
