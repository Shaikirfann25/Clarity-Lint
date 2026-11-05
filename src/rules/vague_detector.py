"""Vague-term detection using a configurable lexicon.

A vague term is a word/phrase that does not give a measurable condition
("soon", "appropriate", "as needed"). To extend: add terms to
DEFAULT_VAGUE_TERMS, or pass your own `lexicon` to detect_vague().
"""
import re
from typing import Dict, Iterable, List, Optional

from .common import make_detection

# Terms about time/frequency: the fix is a number or schedule.
TIME_TERMS = {
    "soon", "promptly", "quickly", "timely", "regularly", "periodically",
    "frequently", "occasionally", "as soon as possible", "fast",
}

DEFAULT_VAGUE_TERMS = (
    # time / frequency
    "soon", "promptly", "quickly", "timely", "regularly", "periodically",
    "frequently", "occasionally", "as soon as possible", "fast",
    # conditions
    "as needed", "as appropriate", "as necessary", "if necessary",
    "when necessary", "if appropriate", "where appropriate", "if needed",
    # degree / quality
    "appropriate", "appropriately", "reasonable", "reasonably", "adequate",
    "adequately", "sufficient", "sufficiently", "user-friendly",
    "easy to use", "efficient", "efficiently", "flexible", "robust",
    "minimal", "significant", "substantial",
    # open-ended lists
    "etc", "and so on", "and the like",
)


def build_vague_pattern(terms: Iterable[str]) -> Optional["re.Pattern"]:
    """Compile a case-insensitive, whole-word pattern; longest terms first."""
    cleaned = sorted({t.strip().lower() for t in terms if t and t.strip()},
                     key=len, reverse=True)
    if not cleaned:
        return None
    alts = []
    for term in cleaned:
        alts.append(r"\s+".join(re.escape(w) for w in term.split()))
    return re.compile(r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])", re.IGNORECASE)


_DEFAULT_PATTERN = build_vague_pattern(DEFAULT_VAGUE_TERMS)


def detect_vague(sentence: str, lexicon: Optional[Iterable[str]] = None) -> List[Dict]:
    """Flag vague terms. `lexicon=None` uses the default list."""
    pattern = _DEFAULT_PATTERN if lexicon is None else build_vague_pattern(lexicon)
    if pattern is None:
        return []
    out = []
    for m in pattern.finditer(sentence):
        term = m.group(0).lower()
        if term in TIME_TERMS:
            hint = "how soon or how often (for example 'within 5 minutes' or 'every 7 days')"
        else:
            hint = "a measurable condition (for example a number, limit, or clear criterion)"
        reason = f'"{m.group(0)}" is vague: it does not say {hint}.'
        out.append(make_detection("vague", sentence, m.start(), m.end(), reason))
    return out
