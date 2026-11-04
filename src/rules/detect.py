"""Main entry point and orchestrator for Clarity Lint rule-based ambiguity detection.

Implements the contract defined in:
- docs/shared_schema.json
- docs/integration_contract.md
- docs/annotation_guide.md (Priority Hierarchy: attachment > pronoun > scope > vague > no_ambiguity)
"""

from typing import Any, Union

from src.rules.attachment import detect_attachment
from src.rules.pronoun import detect_pronoun
from src.rules.scope import detect_scope
from src.rules.vague_detector import detect_vague

# Priority rank order per Annotation Guide Section 5
PRIORITY_RANK: dict[str, int] = {
    "attachment": 0,
    "pronoun": 1,
    "scope": 2,
    "vague": 3,
    "no_ambiguity": 4,
}


def detect_sentence(sentence: str) -> list[dict[str, Any]]:
    """Detect ambiguity in a single sentence across all rule modules.

    Runs each specialized detector and sorts findings by precedence hierarchy:
    attachment > pronoun > scope > vague.

    Args:
        sentence: A single sentence string.

    Returns:
        A list of detection dictionaries adhering to docs/shared_schema.json.
        Returns an empty list [] if no ambiguity is detected.
    """
    if not sentence or not sentence.strip():
        return []

    findings: list[dict[str, Any]] = []

    # Run individual detectors
    att_hits = detect_attachment(sentence)
    if att_hits:
        findings.extend(att_hits)

    pro_hits = detect_pronoun(sentence)
    if pro_hits:
        findings.extend(pro_hits)

    scope_hits = detect_scope(sentence)
    if scope_hits:
        findings.extend(scope_hits)

    vague_hits = detect_vague(sentence)
    if vague_hits:
        findings.extend(vague_hits)

    # Sort according to established precedence hierarchy
    findings.sort(key=lambda d: PRIORITY_RANK.get(d.get("label", "no_ambiguity"), 99))
    return findings


def detect(sentences: Union[list[str], str]) -> list[dict[str, Any]]:
    """Detect ambiguity across sentences following the team integration contract.

    Compatible with:
    - src.integration.pipeline._call_team_rules: passes [sentence] and expects list[dict]
    - Direct list of sentence strings: returns flat list of detections
    - Single string: automatically wrapped as [sentence]

    Args:
        sentences: A list of sentence strings or a single sentence string.

    Returns:
        A list of detection dictionaries, each with schema:
        {
            "source": "rules",
            "label": "attachment" | "pronoun" | "scope" | "vague",
            "span": str | None,
            "confidence": None,
            "reason": str
        }
        Returns [] if no ambiguities are found.
    """
    if isinstance(sentences, str):
        sentences = [sentences]

    if not sentences:
        return []

    all_detections: list[dict[str, Any]] = []
    for sentence in sentences:
        detections = detect_sentence(sentence)
        all_detections.extend(detections)

    return all_detections


def predict_label(sentence: str) -> str:
    """Predict the single highest-priority label for a sentence.

    Used for evaluation benchmarks and confusion matrix calculation.
    Follows priority order: attachment > pronoun > scope > vague > no_ambiguity.

    Args:
        sentence: A sentence string.

    Returns:
        One of: 'attachment', 'pronoun', 'scope', 'vague', 'no_ambiguity'.
    """
    detections = detect_sentence(sentence)
    if not detections:
        return "no_ambiguity"
    return detections[0]["label"]

