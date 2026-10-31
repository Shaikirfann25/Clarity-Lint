"""Vague language detection module for Clarity Lint.

Detects words or phrases that lack a measurable, agreed-upon definition in context
(e.g., 'quickly', 'soon', 'reasonable amount of time', 'adequate').
"""

import re
from typing import Any

# Multi-word vague phrases that signal unmeasured criteria or timelines
VAGUE_PHRASES: list[str] = [
    r"reasonable amount of time",
    r"reasonable understanding",
    r"timely manner",
    r"timely delivery",
    r"as soon as possible",
    r"when you have a chance",
    r"for some time",
    r"too long",
    r"easy to follow",
    r"simple to follow",
    r"robust enough",
    r"clear enough",
    r"high level of accuracy",
    r"high standard of work",
    r"high standard",
    r"high proportion of",
    r"large volume of",
    r"large sample of",
    r"small number of",
    r"moderate improvement",
    r"significant difference",
    r"substantial correlation",
    r"similar conditions",
    r"acceptable safety standards",
    r"professional attitude",
    r"good impression",
    r"realistic effort",
    r"common threats",
    r"proper onboarding",
    r"appropriate format",
    r"appropriately scoped",
    r"relevant compliance training",
    r"competitive price",
    r"somewhat confusing",
    r"clearly written",
    r"key concerns adequately",
    r"reasonably short",
    r"sufficiently detailed",
    r"better approach",
    r"better result",
    r"minimal downtime",
    r"perform well",
    r"expected to be short",
    r"many users",
]

# Single-word vague adverbs, adjectives, and qualifiers
VAGUE_TERMS: list[str] = [
    r"quickly",
    r"soon",
    r"promptly",
    r"timely",
    r"regularly",
    r"frequently",
    r"periodically",
    r"adequately",
    r"adequate",
    r"significantly",
    r"significant",
    r"substantially",
    r"substantial",
    r"efficiently",
    r"efficient",
    r"gracefully",
    r"thoroughly",
    r"thorough",
    r"appropriately",
    r"appropriate",
    r"maintainable",
    r"comprehensive",
    r"intuitive",
    r"compelling",
    r"acceptable",
    r"sufficient",
    r"realistic",
    r"several",
    r"moderate",
    r"reasonable",
    r"helpful",
    r"applicable",
    r"extensive",
    r"better",
]

# Measurable numeric patterns that exempt otherwise vague words (e.g. 'within 200 ms')
MEASURABLE_PATTERN = re.compile(
    r"\b(?:within\s+\d+|under\s+\d+|at\s+least\s+\d+|at\s+most\s+\d+|\d+\s*percent|\d+\s*(?:milliseconds|ms|seconds|minutes|hours|days|weeks|months|years))\b",
    re.IGNORECASE,
)

# Overrides that are still vague even if numbers appear elsewhere in sentence
UNCONDITIONAL_VAGUE = re.compile(
    r"\b(reasonable amount of time|as soon as possible|promptly|timely manner)\b",
    re.IGNORECASE,
)


def detect_vague(text: str) -> list[dict[str, Any]]:
    """Detect vague language in a sentence.

    Args:
        text: Sentence text to analyze.

    Returns:
        List of detection dictionaries strictly complying with shared_schema.json:
        [{"source": "rules", "label": "vague", "span": str, "confidence": None, "reason": str}]
    """
    if not text or not text.strip():
        return []

    # Check if sentence contains measurable numeric thresholds
    if MEASURABLE_PATTERN.search(text) and not UNCONDITIONAL_VAGUE.search(text):
        return []

    # Check multi-word phrases first (higher specificity)
    for phrase_pat in VAGUE_PHRASES:
        match = re.search(r"\b" + phrase_pat + r"\b", text, re.IGNORECASE)
        if match:
            span = match.group(0)
            return [{
                "source": "rules",
                "label": "vague",
                "span": span,
                "confidence": None,
                "reason": f"'{span}' lacks a measurable threshold or objective definition."
            }]

    # Check individual vague terms
    for term_pat in VAGUE_TERMS:
        match = re.search(r"\b" + term_pat + r"\b", text, re.IGNORECASE)
        if match:
            span = match.group(0)
            return [{
                "source": "rules",
                "label": "vague",
                "span": span,
                "confidence": None,
                "reason": f"The term '{span}' is subjective or unmeasured without concrete criteria."
            }]

    return []

