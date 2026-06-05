from __future__ import annotations

import re
from typing import Any


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    """Return a compact, stripped text representation safe for embeddings."""
    if value is None:
        return ""
    text = str(value)
    return _WHITESPACE_RE.sub(" ", text).strip()


def has_text(value: Any) -> bool:
    return normalize_text(value) != ""
