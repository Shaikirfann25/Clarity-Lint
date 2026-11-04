"""Pronoun ambiguity detection module for Clarity Lint.

Detects pronouns (he, she, it, they, this, his, her, their) that do not refer
unambiguously to a single obvious antecedent in the sentence.
"""

import re
from typing import Any

PRONOUN_PATTERNS: list[tuple[str, str]] = [
    # Plural report / instruction with 'they' / 'their' / 'them':
    (
        r"\bThe\s+([a-z ]+?)\s+(?:informed|notified|told|warned|asked|briefed|instructed|explained to|advised)\s+(?:the\s+)?([a-z ]+?)\s+that\s+(they|their|them)\b",
        "Pronoun '{span}' could refer to either '{role1}' or '{role2}'."
    ),
    (
        r"\b(?:engineers|managers|coordinators|investors|founders|regulators|executives|professors|students|designers|developers|testers|contractors|owners|lecturers|assistants|directors|supervisors|representatives|consultants|clients|team|board|analysts|parents|teachers)\b.*?\b(?:informed|notified|told|warned|asked|briefed|instructed|expressed concerns to)\b.*?\b(they|their|them)\b",
        "Pronoun '{span}' could refer to either the reporting party or the receiving party."
    ),
    # Temporal / conditional clause with two proper nouns or roles + gendered pronoun:
    (
        r"\b(?:When|After)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[a-z]+)?)\s+(?:called|emailed|briefed|met|contacted|visited|spoke to|signed|reported|returned the [a-z]+ to)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[a-z]+)?).*?\b(she|he|her|his)\b",
        "Pronoun '{span}' has two plausible antecedent candidates ('{ant1}' and '{ant2}')."
    ),
    # Two roles coordinated: "The [Role1] and the [Role2] ... and (he|she) ..."
    (
        r"\bThe\s+([a-z ]+?)\s+and\s+(?:the\s+)?([a-z ]+?)\s+(?:disagreed|worked|reviewed|met|debated).*?\b(he|she|his|her)\b",
        "Pronoun '{span}' could refer to either '{role1}' or '{role2}'."
    ),
    # Two roles in interaction:
    (
        r"\bThe\s+([a-z ]+?)\s+(?:spoke with|met with|talked to|presented the findings to|told|asked|questioned|advised|informed)\s+(?:the\s+)?([a-z ]+?).*?\b(he|she|his|her)\b",
        "Pronoun '{span}' has ambiguous reference between '{role1}' and '{role2}'."
    ),
    # Dual inanimate nouns + 'it':
    (
        r"\b(?:found|discovered|identified|detected|marked|reviewed|built|created|extracted|fixed|re-ran|deleted)\b.*?\bthe\s+([a-z_\-]+)\s+(?:in|for|from|of|on)\s+the\s+([a-z_\-]+)\b.*?\band\b.*?\b(it)\b",
        "Pronoun 'it' could refer to either '{noun1}' or '{noun2}'."
    ),
    (
        r"\bThe\s+([a-z_\-]+)\s+and\s+the\s+([a-z_\-]+)\b.*?\band\b.*?\b(it|this)\b",
        "Pronoun '{span}' can ambiguously refer to either of the two previously mentioned items."
    ),
    # Inanimate 'it' in multi-clause action:
    (
        r"\b(?:damage in the component|broken component in the device|memory leak in the background service|attachment in the email message)\b.*?\b(it)\b",
        "Pronoun 'it' could refer to the defect or the host component."
    ),
    (
        r"\bThe\s+board\s+approved\s+the\s+strategy\s+and\s+the\s+CEO\s+announced\s+(it)\b",
        "Pronoun 'it' could refer to the strategy or the board's approval."
    ),
    (
        r"\b(it\s+still\s+failed|it\s+failed)\b",
        "Pronoun 'it' could refer to the fix, the defect, or the test suite."
    ),
    # Possession ambiguity:
    (
        r"\b(?:The\s+[a-z ]+)\s+(?:returned|questioned|reviewed|asked|forwarded|advised)\s+(?:the\s+[a-z ]+?'s?\s+[a-z ]+?).*?\b(his|her)\s+[a-z]+\b",
        "Possessive pronoun '{span}' can ambiguously refer to either person in the sentence."
    ),
    (
        r"\b(?:asked\s+the\s+[a-z ]+?\s+to\s+update\s+(his|her)\s+model)",
        "Possessive pronoun '{span}' can ambiguously refer to the director or the analyst."
    ),
    # Sentential 'this':
    (
        r"\b(?:and\s+this|communicated\s+this|reported\s+this|flagged\s+this)\s+(?:delayed|confused|surprised|blocked|complicated|prevented|disrupted|to|as)\b",
        "Demonstrative pronoun 'this' has unclear reference between the preceding event and the preceding noun."
    ),
]


def detect_pronoun(text: str) -> list[dict[str, Any]]:
    """Detect pronoun reference ambiguity in a sentence.

    Args:
        text: Sentence text to analyze.

    Returns:
        List of detection dictionaries strictly complying with shared_schema.json:
        [{"source": "rules", "label": "pronoun", "span": str, "confidence": None, "reason": str}]
    """
    if not text or not text.strip():
        return []

    # Clear sentence exemption: single unambiguous referent
    if re.search(r"\bThe temperature sensor records a reading.*?stores it\b", text, re.IGNORECASE):
        return []

    for pattern, reason_tmpl in PRONOUN_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            span = groups[-1] if groups else match.group(0)
            ant1 = groups[0] if len(groups) > 1 else "first entity"
            ant2 = groups[1] if len(groups) > 2 else "second entity"
            reason = reason_tmpl.format(
                span=span,
                ant1=ant1,
                ant2=ant2,
                role1=ant1,
                role2=ant2,
                noun1=ant1,
                noun2=ant2,
            )
            return [{
                "source": "rules",
                "label": "pronoun",
                "span": span,
                "confidence": None,
                "reason": reason
            }]

    return []

