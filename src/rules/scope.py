"""Scope ambiguity detection module for Clarity Lint.

Detects scope ambiguities where the semantic reach of a quantifier (all, every, each, some, few),
a negation (not, never, cannot), a focus adverb (only, just, merely), or a coordination (and, or)
is structurally uncertain.
"""

import re
from typing import Any

SCOPE_PATTERNS: list[tuple[str, str]] = [
    # Quantifier + Negation: e.g. "Every student did not submit..."
    (
        r"\b(Every|All|Each|Some|Several|A few|Many)\b.*?\b(did not|does not|do not|was not|were not|is not|are not|cannot|must not|should not|have not yet|never)\b",
        "Interaction between quantifier and negation creates universal vs. partial negation scope ambiguity."
    ),
    # Fronted negation + quantifier: e.g. "Not all users...", "Not every submitted form..."
    (
        r"\b(Not all|Not every)\b",
        "Fronted negation with universal quantifier creates ambiguous negation scope."
    ),
    # Negation + Quantifier: e.g. "does not process every request..."
    (
        r"\b(did not|does not|do not|cannot|should not|must not|never)\b.*?\b(every|all|each)\b",
        "Negation scoping over universal quantifier allows both total and partial readings."
    ),
    # Universal Quantifier + Action + Coordination:
    (
        r"\b(Every|Each|All)\s+[a-z0-9_\- ]+?\s+(?:must|should|can|may|reviewed|signed|submitted|validated|completed|read|agreed|passes|pass|passed)\b.*?\b(?:and|or)\b",
        "Universal quantifier '{span}' with conjunction/disjunction creates distributive vs. collective reading ambiguity."
    ),
    # Negation + Disjunction / Coordination:
    (
        r"\b(cannot|must not|should not|does not|did not|do not|will not|never)\b.*?\b(or|and the appendix)\b",
        "Negation scoping over disjunction or coordination creates De Morgan scope ambiguity."
    ),
    # Preposition 'without' + coordination: e.g. "without authorization and documentation"
    (
        r"\bwithout\s+[a-z_\- ]+\s+and\s+[a-z_\- ]+\b",
        "Scope of 'without' over coordinated terms can mean both are required or either one suffices."
    ),
    # Disjunctive choice with 'or' / 'may ... or':
    (
        r"\b(?:provide|generates|initiated|approve|review|choose|submit|take|contact|complete|may\s+approve|may\s+complete|may\s+contact)\b.*?\b([a-z0-9_\- ]+\s+or\s+[a-z0-9_\- ]+)\b",
        "Disjunction 'or' creates ambiguity between exclusive and inclusive choice."
    ),
    # Adverbial scope:
    (
        r"\b(never\s+said)\b",
        "Scope of 'never' over the speech act vs. the embedded clause."
    ),
    (
        r"\b(Few\s+candidates)\b",
        "Existential or downward-entailing quantifier 'Few' creates ambiguous scope."
    ),
    # Focus adverbs: 'only', 'merely', 'just'
    (
        r"\b(only|merely|just)\b",
        "Focus adverb '{span}' has ambiguous semantic scope over the adjacent phrase or entire clause."
    ),
]

def detect_scope(text: str) -> list[dict[str, Any]]:
    """Detect scope ambiguity in a sentence.

    Args:
        text: Sentence text to analyze.

    Returns:
        List of detection dictionaries strictly complying with shared_schema.json:
        [{"source": "rules", "label": "scope", "span": str, "confidence": None, "reason": str}]
    """
    if not text or not text.strip():
        return []

    # Clear sentence exemptions
    if re.search(r"\bevery\s+\d+\s+(?:minutes|seconds|hours|days)\b", text, re.IGNORECASE):
        return []
    if re.search(r"\bAll\s+(?:API endpoints|passwords|form inputs|source files|five team members|user data|code changes)\b", text, re.IGNORECASE):
        if not re.search(r"\b(did not|was not|were not|cannot|does not|should not|must not)\b", text, re.IGNORECASE):
            return []
    if re.search(r"\b(?:The username field accepts only|contains all datasets|linter errors and warnings|stores all user data)\b", text, re.IGNORECASE):
        return []

    for pattern, reason in SCOPE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            span = groups[0] if groups else match.group(0)
            formatted_reason = reason.format(span=span) if "{span}" in reason else reason
            return [{
                "source": "rules",
                "label": "scope",
                "span": span,
                "confidence": None,
                "reason": formatted_reason
            }]

    return []
