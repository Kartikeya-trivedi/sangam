"""Name normalization + similarity for the matching engine.

Indian names transliterate inconsistently ("Ajay" / "Ajeet", honorifics, surname-as-given).
We normalize aggressively, then blend an edit-distance ratio with a phonetic-equality bonus so
"Ajay Kumar" vs "Ajeet Kumar" scores ~0.6 (a hint), not 0.0 and not a false 1.0.

rapidfuzz provides fast Levenshtein-based ratios; we add a lightweight Soundex for the
phonetic signal (no extra dependency).
"""
from __future__ import annotations

import re

from rapidfuzz import fuzz

# Honorifics / relationship words / common surname suffixes that add no identity signal.
_HONORIFICS = {
    "shri", "sri", "smt", "smt.", "shrimati", "kumari", "km", "ji", "baba", "mata",
    "mr", "mrs", "ms", "dr", "shree", "thiru", "selvi",
}
_TITLECASE_RE = re.compile(r"[^a-z\s]")


def normalize_name(name: str | None) -> str:
    """Lowercase, strip honorifics + non-alpha, collapse whitespace. '' when empty/None."""
    if not name:
        return ""
    s = name.strip().lower()
    s = _TITLECASE_RE.sub(" ", s)  # drop digits/punctuation/native script
    tokens = [t for t in s.split() if t and t not in _HONORIFICS]
    return " ".join(tokens)


def soundex(token: str) -> str:
    """Classic Soundex code (letter + 3 digits). Empty string for empty input."""
    token = re.sub(r"[^a-z]", "", token.lower())
    if not token:
        return ""
    codes = {**dict.fromkeys("bfpv", "1"), **dict.fromkeys("cgjkqsxz", "2"),
             **dict.fromkeys("dt", "3"), "l": "4", **dict.fromkeys("mn", "5"), "r": "6"}
    first = token[0]
    tail, prev = [], codes.get(first, "")
    for ch in token[1:]:
        c = codes.get(ch, "")
        if c and c != prev:
            tail.append(c)
        if ch not in "hw":
            prev = c
    return (first.upper() + "".join(tail) + "000")[:4]


def _phonetic_key(name: str) -> tuple[str, ...]:
    return tuple(soundex(t) for t in name.split() if t)


def name_similarity(a: str | None, b: str | None) -> float | None:
    """0..1 similarity, or None when EITHER name is absent (weight redistributes upstream).

    Blend: token-sorted edit ratio (handles word order / surname swaps) with a phonetic bonus.
    """
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return None
    if na == nb:
        return 1.0
    edit = fuzz.token_sort_ratio(na, nb) / 100.0
    pa, pb = _phonetic_key(na), _phonetic_key(nb)
    phonetic = 0.0
    if pa and pb:
        shared = len(set(pa) & set(pb))
        phonetic = shared / max(len(set(pa)), len(set(pb)))
    # Edit distance leads; phonetic agreement lifts near-homophones.
    score = 0.7 * edit + 0.3 * phonetic
    return round(min(1.0, score), 4)
