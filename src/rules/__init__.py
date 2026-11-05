"""Rule-based ambiguity detectors (Person 2).

Entry point: src.rules.detect.detect
"""

from src.rules.attachment import detect_attachment
from src.rules.common import LABELS
from src.rules.detect import detect, detect_sentence, predict_label, primary_label
from src.rules.pronoun import detect_pronoun
from src.rules.scope import detect_scope
from src.rules.vague_detector import detect_vague

__all__ = [
    "detect",
    "detect_sentence",
    "predict_label",
    "primary_label",
    "detect_attachment",
    "detect_pronoun",
    "detect_scope",
    "detect_vague",
    "LABELS",
]
