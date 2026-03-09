"""Utility functions for the application."""

from config import LOG_LEVEL, DEBUG


def log(message: str, level: str = None):
    """Log a message with optional level override."""
    lvl = level or LOG_LEVEL
    if DEBUG:
        print(f"[{lvl}] {message}")


def format_response(data: dict) -> str:
    """Format data as a simple JSON-like string."""
    parts = [f"{k!r}: {v!r}" for k, v in data.items()]
    return "{" + ", ".join(parts) + "}"
