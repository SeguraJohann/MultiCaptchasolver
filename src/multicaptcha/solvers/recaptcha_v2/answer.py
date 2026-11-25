import re


def normalize_answer(text: str) -> str:
    """Lowercase, drop punctuation and collapse whitespace."""
    return " ".join(re.sub(r"[^a-z0-9\s]", "", text.lower()).split())
