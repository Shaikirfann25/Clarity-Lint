"""Shared entry point for the rule-based detectors (Person 2).

    from src.rules.detect import detect
    records = detect(["The admin monitors the user with the sensor."])

Each record follows the team's shared schema (rules fill only `predictions`):
    {"sentence_id": "S001", "text": "...", "predictions": [ {...}, ... ]}
`predictions` is an empty list when nothing is flagged. Output is deterministic.

CLI:  python -m src.rules.detect "Some sentence."
"""
import json
import sys
from typing import Dict, Iterable, List, Sequence, Union

from .attachment import detect_attachment
from .pronoun import detect_pronoun
from .scope import detect_scope
from .vague_detector import detect_vague

RULES = (
    ("vague", detect_vague),
    ("attachment", detect_attachment),
    ("scope", detect_scope),
    ("pronoun", detect_pronoun),
)

# When a sentence is flagged with several labels and a single label is needed
# (e.g. to compare with a single-label classifier), the first one in this list
# wins. Agree on this with Person 3 / Person 5 before final evaluation.
PRIORITY = ("attachment", "scope", "pronoun", "vague")


def detect_sentence(text: str, enabled: Sequence[str] = None) -> List[Dict]:
    """Run all (or the `enabled`) rule modules on one sentence."""
    preds: List[Dict] = []
    for name, fn in RULES:
        if enabled is None or name in enabled:
            preds.extend(fn(text))
    # deterministic order: position in sentence, then label, then span
    preds.sort(key=lambda p: (text.find(p["span"]), p["label"], p["span"]))
    return preds


def detect(sentences: Iterable[Union[str, Dict]], enabled: Sequence[str] = None) -> List[Dict]:
    """Detect ambiguity in a list of sentences.

    Each item is either a string, or a dict with "text" (and optional
    "sentence_id" / "gold_label", which are passed through).
    """
    records = []
    for i, item in enumerate(sentences, start=1):
        if isinstance(item, str):
            item = {"text": item}
        text = item.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Item {i} has no string 'text': {item!r}")
        preds = detect_sentence(text, enabled)
        rec = {"sentence_id": item.get("sentence_id", f"S{i:03d}"), "text": text,
               "predictions": preds}
        if "gold_label" in item:
            rec["gold_label"] = item["gold_label"]
        # Compatibility with flat detection consumers (e.g. pipeline adapter)
        if preds:
            rec["label"] = preds[0]["label"]
            rec["span"] = preds[0]["span"]
            rec["reason"] = preds[0]["reason"]
            rec["source"] = preds[0].get("source", "rules")
            rec["confidence"] = preds[0].get("confidence", None)
        else:
            rec["label"] = "no_ambiguity"
            rec["span"] = None
            rec["reason"] = None
            rec["source"] = "rules"
            rec["confidence"] = None
        records.append(rec)
    return records


def predict_label(sentence: str) -> str:
    """Predict the single highest-priority label for a sentence."""
    recs = detect([sentence])
    if not recs:
        return "no_ambiguity"
    return primary_label(recs[0])


def primary_label(record: Dict, priority: Sequence[str] = PRIORITY) -> str:
    """Collapse a record to one label ('no_ambiguity' if nothing was flagged)."""
    found = {p["label"] for p in record["predictions"]}
    for label in priority:
        if label in found:
            return label
    return "no_ambiguity"


if __name__ == "__main__":
    texts = sys.argv[1:] or ["The admin monitors the user with the sensor."]
    print(json.dumps(detect(texts), indent=2, ensure_ascii=False))
