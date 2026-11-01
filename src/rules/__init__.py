"""Clarity Lint - Rule-Based Ambiguity Detection Package (Person 2).

This package implements handcrafted linguistic rules for detecting ambiguities
in English sentences according to the Clarity Lint shared schema and annotation guide.

Exported functions:
- detect: Batch/single sentence ambiguity detector conforming to integration contract.
- detect_sentence: Single sentence ambiguity detector.
- predict_label: Single label predictor following the precedence hierarchy.
- detect_attachment: Specialized detector for attachment ambiguity.
- detect_pronoun: Specialized detector for pronoun ambiguity.
- detect_scope: Specialized detector for scope ambiguity.
- detect_vague: Specialized detector for vague language.
"""

from src.rules.attachment import detect_attachment
from src.rules.detect import detect, detect_sentence, predict_label
from src.rules.pronoun import detect_pronoun
from src.rules.scope import detect_scope
from src.rules.vague_detector import detect_vague

__all__ = [
    "detect",
    "detect_sentence",
    "predict_label",
    "detect_attachment",
    "detect_pronoun",
    "detect_scope",
    "detect_vague",
]

