"""Shared BM25 tokenization so the index-build side and the query side never drift apart."""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())
