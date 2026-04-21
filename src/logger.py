"""
logger.py — Centralized structured logging for Binance Futures Bot
All modules import from here to write to bot.log + colored console output.
"""

import logging
import colorlog
import os

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot.log")


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with:
      - Colored console handler (DEBUG+)
      - Structured file handler writing to bot.log (DEBUG+)
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Avoid duplicate handlers on re-import

    logger.setLevel(logging.DEBUG)

    # ── Console handler (colored) ──────────────────────────────────────────
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s: %(message)s%(reset)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        },
    )
    console_handler.setFormatter(console_formatter)

    # ── File handler (plain structured) ───────────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
