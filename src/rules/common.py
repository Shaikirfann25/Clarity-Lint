"""Shared helpers for the rule-based detectors (Person 2).

Every detector returns a list of "prediction" dicts in the team's agreed shape:

    {"source": "rules", "label": "<label>", "span": "<exact substring>",
     "confidence": None, "reason": "<why this may be ambiguous>"}

Spans are always sliced from the ORIGINAL sentence, so they are exact substrings.
Confidence is always None: rules give evidence, not probabilities.
"""
from typing import Dict

SOURCE = "rules"
LABELS = ("vague", "attachment", "scope", "pronoun")


def make_detection(label: str, sentence: str, start: int, end: int, reason: str) -> Dict:
    """Build one prediction dict; the span is sliced from the original text."""
    if label not in LABELS:
        raise ValueError(f"Unknown label: {label!r}")
    return {
        "source": SOURCE,
        "label": label,
        "span": sentence[start:end],
        "confidence": None,
        "reason": reason,
    }
