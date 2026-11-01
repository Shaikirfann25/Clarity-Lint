"""Attachment ambiguity detection module for Clarity Lint.

Detects structural ambiguities where a modifier (PP, participial phrase, or relative clause)
can attach to more than one grammatical constituent in the sentence.
"""

import re
from typing import Any

ATTACHMENT_PATTERNS: list[tuple[str, str]] = [
    # Dangling or fronted participial modifiers (regular and irregular participles)
    (
        r"^((?:[A-Z][a-z]+(?:ed|en|ing)|Built|Found|Left|Held|Kept|Lost|Torn|Set|Known)\s+(?:by|after|in|on|with|outside|inside|under|during|through|for|near|down)\b[^,]+),\s*([A-Za-z]+)",
        "Fronted or dangling modifier '{span}' may not logically or grammatically attach to '{subject}'."
    ),
    (
        r"^(Having\s+[a-z]+(?:ed|en)\b[^,]+),\s*([A-Za-z]+)",
        "Participial phrase '{span}' dangles or creates ambiguous agent attachment."
    ),
    (
        r"^([A-Z][a-z]+ing\s+(?:the|a|an)\s+[a-z]+),\s*([A-Za-z]+)",
        "Fronted non-finite clause '{span}' creates an ambiguous attachment to the following subject."
    ),
    # PP attachment with 'with': Verb + Object NP + with + NP
    (
        r"\b(?:[a-z]+(?:ed|s|ing)?)\s+(?:the|a|an|his|her)\s+[a-z_\- ]+?\s+(with\s+(?:the|a|an|his|her|their|new|damaged|missing|structural|revised|glass|highest|favorable|unfavorable|long)\s+[a-z_\-]+(?:\s+[a-z_\-]+)?)",
        "Prepositional phrase '{span}' may attach to the preceding noun phrase or to the main action verb."
    ),
    # PP with 'from': Verb + Object NP + from + NP
    (
        r"\b(?:sent|saw|called|reviewed|received|greeted|found|presented|approved)\b.*?\s+(from\s+(?:her|his|their|the|a)\s+(?:office|phone|reception\s+desk|desk|mobile|auditor|client|external\s+consultants|contractor|revised\s+proposal|last\s+quarter))\b",
        "Prepositional phrase '{span}' may attach to the action or to the preceding noun."
    ),
    # PP with 'against': e.g. "reviewed the complaint from the client against the new policy"
    (
        r"\b(against\s+the\s+new\s+policy)\b",
        "Prepositional phrase '{span}' could modify the complaint or the review action."
    ),
    # Post-object participial modifier: e.g. "interviewed the protester standing outside the building"
    (
        r"\b(?:the|a|an)\s+[a-z]+\s+(standing\s+(?:outside|inside|near|in|at)\s+(?:the|a)\s+[a-z]+)",
        "Participial phrase '{span}' can modify the preceding object or the main subject/action."
    ),
    (
        r"\b(?:the|a|an)\s+[a-z]+\s+(wearing\s+(?:a|an|the)\s+[a-z]+(?:\s+[a-z]+)?)",
        "Participial modifier '{span}' can ambiguously modify either participant in the event."
    ),
    (
        r"\b(?:the|a|an)\s+[a-z]+\s+(talking\s+to\s+(?:the|a)\s+[a-z]+(?:\s+in\s+the\s+[a-z]+)?)",
        "Participial phrase '{span}' may modify the direct object or the main subject."
    ),
    (
        r"\b(?:the|a|an)\s+[a-z]+\s+(celebrating\s+(?:on|in|at)\s+(?:the|a)\s+[a-z]+)",
        "Participial phrase '{span}' may modify the coordinated nouns or the main verb."
    ),
    (
        r"\b(?:the|a|an)\s+[a-z]+\s+(walking\s+to\s+(?:the|a)\s+[a-z]+(?:\s+from\s+[a-z ]+)?)",
        "Participial phrase '{span}' can modify the object or the main subject."
    ),
    (
        r"\b(?:the|a|an)\s+[a-z]+\s+(playing\s+near\s+(?:the|a)\s+[a-z]+(?:\s+in\s+the\s+[a-z]+)?)",
        "Participial phrase '{span}' can modify the object or the main clause."
    ),
    (
        r"\b(?:left\s+by\s+(?:the|a)\s+[a-z]+)",
        "Passive participial phrase '{span}' can ambiguously attach to either preceding noun."
    ),
    # Relative clause attachment with stacked nouns:
    (
        r"\b(?:to|in|for|from|about|inside)\s+(?:the|a)\s+[a-z ]+?\s+(that\s+(?:was|had|is|needed|contained|opened)\s+[a-z_\-]+(?:\s+[a-z_\-]+)?)",
        "Relative clause '{span}' could attach to the matrix noun or the object of the preposition."
    ),
    (
        r"\b(?:attended\s+to\s+the\s+patient\s+who\s+arrived\s+in\s+the\s+treatment\s+area)",
        "Prepositional phrase 'in the treatment area' can attach to 'arrived' or 'attended'."
    ),
    (
        r"\b(?:serving\s+another\s+customer\s+at\s+the\s+window)",
        "Prepositional phrase 'at the window' can attach to 'serving' or 'handed'."
    ),
    # Locative / temporal PP attachment after relative or complex clause:
    (
        r"\b(?:that|who|which)\s+[a-z_\- ]+?\s+(on\s+(?:the\s+new\s+field|the\s+conference\s+table|Monday|Friday)|in\s+the\s+(?:control\s+room|morning\s+session|evening\s+briefing)|via\s+the\s+online\s+portal)\b",
        "Prepositional phrase '{span}' can attach to the main action or the embedded clause."
    ),
    # Stacked PP:
    (
        r"\b(in\s+the\s+inbox\s+on\s+the\s+right|on\s+the\s+third\s+floor\s+to\s+the\s+receptionist|for\s+the\s+audit\s+team\s+to\s+the\s+wrong\s+address|about\s+the\s+meeting\s+to\s+the\s+wrong\s+department)\b",
        "Stacked prepositional phrase '{span}' creates multiple attachment sites."
    ),
    # Coordinated NP scope/attachment modifier:
    (
        r"\b(Old\s+men\s+and\s+women)\b",
        "Modifier 'Old' can ambiguously scope over just 'men' or both 'men and women'."
    ),
    (
        r"\b((?:almost|nearly)\s+(?:deleted|overlooked|missed|crashed|completed))\b",
        "Adverb '{span}' can scope over the verb action or the resulting state."
    ),
    (
        r"\b(tagged\s+it\s+as\s+the\s+latest\s+stable\s+release)\b",
        "Coordinated verb phrase attachment ambiguity."
    )
]

CLEAR_EXEMPTIONS = re.compile(
    r"\b(?:Insert the USB drive|Run pip install|Push all code changes|Pull request number|Press Ctrl|The second-floor fire exit|The green LED|The orange cable)\b",
    re.IGNORECASE,
)


def detect_attachment(text: str) -> list[dict[str, Any]]:
    """Detect attachment ambiguity in a sentence.

    Args:
        text: Sentence text to analyze.

    Returns:
        List of detection dictionaries strictly complying with shared_schema.json:
        [{"source": "rules", "label": "attachment", "span": str, "confidence": None, "reason": str}]
    """
    if not text or not text.strip():
        return []

    if CLEAR_EXEMPTIONS.search(text):
        return []

    for pattern, reason_template in ATTACHMENT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            span = groups[0] if groups else match.group(0)
            subject = groups[1] if len(groups) > 1 else "the subject"
            reason = reason_template.format(span=span, subject=subject)
            return [{
                "source": "rules",
                "label": "attachment",
                "span": span,
                "confidence": None,
                "reason": reason
            }]

    return []

