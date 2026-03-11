"""Token counting utilities (heuristic with optional tiktoken)."""

from __future__ import annotations

import math


def count_tokens(text: str) -> int:
    """
    Count tokens in text.

    - If `tiktoken` is installed, uses it (cl100k_base).
    - Otherwise uses a rough heuristic: ~4 chars/token.
    """
    try:
        import tiktoken  # type: ignore

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # Simple heuristic that works offline. Good enough for a demo metric.
        return int(math.ceil(len(text) / 4.0))

