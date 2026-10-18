"""Lightweight text retrieval over USDA food-description metadata.

The precomputed FAISS/CLIP artifacts are retained for offline experiments, but
the deployed API deliberately does not load them: loading CLIP to make a query
vector would defeat text-only, low-memory operation.
"""

from __future__ import annotations

import pickle
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
METADATA_PATH = DATA_DIR / "usda_metadata.pkl"
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _normalise(value: str) -> str:
    return " ".join(_TOKEN_RE.findall(value.lower()))


@lru_cache(maxsize=1)
def _food_metadata() -> tuple[dict, ...]:
    with METADATA_PATH.open("rb") as source:
        return tuple(pickle.load(source))


def _score(query: str, description: str) -> tuple[float, bool]:
    normalised_description = _normalise(description)
    if query == normalised_description:
        return 1.0, True
    query_tokens = set(query.split())
    description_tokens = set(normalised_description.split())
    overlap = len(query_tokens & description_tokens) / len(query_tokens)
    phrase_bonus = 0.35 if query in normalised_description else 0.0
    similarity = SequenceMatcher(None, query, normalised_description).ratio()
    return (0.55 * overlap) + (0.30 * similarity) + phrase_bonus, False


def search_food_by_text(query: str, top_k: int = 5) -> list[dict]:
    """Return the best USDA food-description matches for a user-entered name."""
    normalised_query = _normalise(query)
    if not normalised_query or top_k < 1:
        return []
    scored = []
    for food in _food_metadata():
        score, exact_match = _score(normalised_query, food["Main food description"])
        if score > 0:
            scored.append((score, exact_match, food))
    scored.sort(key=lambda item: (item[1], item[0]), reverse=True)
    return [
        {"Food code": item[2]["Food code"], "Main food description": item[2]["Main food description"],
         "score": round(item[0], 4), "exact_match": item[1]}
        for item in scored[:top_k]
    ]
