"""Integration adapters for Clarity Lint.

The demo fallback is intentionally transparent and is not a replacement for teammates'
rule/model/explanation modules. Optional imports are attempted only when those modules exist.
"""
from __future__ import annotations
import re, time
from typing import Any

LABELS = {"no_ambiguity", "vague", "attachment", "scope", "pronoun"}
VAGUE_TERMS = ["soon", "appropriate", "regularly", "as needed", "reasonable", "promptly", "adequate", "timely"]

def demo_mode_label() -> str:
    return "DEMO / illustrative fallback"

def _demo_detect(sentence: str) -> list[dict[str, Any]]:
    text = sentence
    low = text.lower()
    found = []
    for term in VAGUE_TERMS:
        match = re.search(r"\b" + re.escape(term) + r"\b", text, flags=re.I)
        if match:
            found.append({"source":"demo_rules","label":"vague","span":match.group(0),
                          "confidence":None,"reason":f"'{match.group(0)}' may lack a measurable threshold or timeframe."})
            break
    if re.search(r"\bwith\s+(?:the|a|an)\s+\w+", text, re.I):
        m = re.search(r"\bwith\s+(?:the|a|an)\s+\w+", text, re.I)
        found.append({"source":"demo_rules","label":"attachment","span":m.group(0),
                      "confidence":None,"reason":"This prepositional phrase may attach to different parts of the sentence; context is needed."})
    if re.search(r"\b(it|they|them|their|he|she|this|that)\b", text, re.I):
        m = re.search(r"\b(it|they|them|their|he|she|this|that)\b", text, re.I)
        found.append({"source":"demo_rules","label":"pronoun","span":m.group(0),
                      "confidence":None,"reason":"The reference may be unclear if more than one antecedent is plausible."})
    if re.search(r"\bnot\b.*\band\b|\ball\b.*\band\b", low):
        m = re.search(r"\bnot\b.*\band\b|\ball\b.*\band\b", text, re.I)
        found.append({"source":"demo_rules","label":"scope","span":m.group(0),
                      "confidence":None,"reason":"The scope of a modifier or coordination may need to be made explicit."})
    # Keep demo output conservative-ish: only the first heuristic hit is used for this demo.
    # Real team detector can emit multiple findings with better context checks.
    return found[:2]

def _demo_explain(sentence: str, detections: list[dict[str, Any]]) -> tuple[str, list[str], list[str]]:
    if not detections:
        return ("No configured demo pattern flagged this sentence. That does not prove it is unambiguous.", [], [])
    label = detections[0]["label"]
    if label == "vague":
        return ("The flagged term may leave timing, quality, or required conditions open to interpretation.",
                ["Different readers may apply different thresholds or deadlines."],
                ["Replace the vague term with a measurable threshold or an agreed deadline (only after the intended value is confirmed)."])
    if label == "attachment":
        return ("The phrase may modify more than one part of the sentence, changing who uses what or how an action is performed.",
                ["The actor uses the object as a tool.", "The object is associated with another entity in the sentence."],
                ["If the actor uses the object: state that relationship directly.", "If the object belongs to the other entity: name that relationship directly."])
    if label == "pronoun":
        return ("A pronoun may refer to more than one entity. Naming the intended entity avoids guessing.",
                ["The pronoun refers to the first mentioned entity.", "The pronoun refers to another mentioned entity."],
                ["Replace the pronoun with the intended person's or system's name."])
    return ("A modifier or coordinated phrase may apply to more than one part of the sentence.",
            ["The modifier applies to the whole coordinated group.", "The modifier applies to only one part of the group."],
            ["Rewrite the sentence so the intended scope is explicit."])

def _call_team_rules(sentence: str):
    try:
        from src.rules.detect import detect
        result = detect([sentence])
        if isinstance(result, list):
            return result
    except (ImportError, AttributeError, TypeError):
        pass
    return None

def _call_team_model(sentence: str):
    try:
        from src.model.predict import predict
        result = predict([sentence])
        if isinstance(result, list):
            return result
    except (ImportError, AttributeError, TypeError):
        pass
    return None

def _call_team_explanations(sentence: str, detections):
    try:
        from src.explanations.explain import explain
        result = explain(sentence, detections)
        if isinstance(result, dict):
            return result
    except (ImportError, AttributeError, TypeError):
        pass
    return None

def analyze_text(sentence: str) -> dict[str, Any]:
    start = time.perf_counter()
    rule_output = _call_team_rules(sentence)
    if rule_output is None:
        detections = _demo_detect(sentence)
        mode = "demo_fallback"
    else:
        detections = rule_output
        mode = "team_rules_connected"
    # Keep schema normalization at the integration boundary.
    normalized = []
    for d in detections or []:
        label = d.get("label", "no_ambiguity")
        if label not in LABELS: label = "no_ambiguity"
        normalized.append({
            "source": d.get("source", "rules" if mode == "team_rules_connected" else "demo_rules"),
            "label": label, "span": d.get("span"), "confidence": d.get("confidence"),
            "reason": d.get("reason", "Possible ambiguity; review in context.")
        })
    explanation_output = _call_team_explanations(sentence, normalized)
    if explanation_output:
        explanation = explanation_output.get("explanation", "Review the flagged evidence.")
        readings = explanation_output.get("readings", [])
        rewrites = explanation_output.get("rewrites", [])
    else:
        explanation, readings, rewrites = _demo_explain(sentence, normalized)
    # If classifier exists, expose its output separately; never merge its label into the rules list.
    model_output = _call_team_model(sentence)
    return {
        "sentence_id": None, "text": sentence, "detections": normalized,
        "model_predictions": model_output if model_output is not None else [],
        "explanation": explanation, "readings": readings, "rewrites": rewrites,
        "mode": mode, "latency_ms": (time.perf_counter()-start)*1000
    }

def split_sentences(text: str) -> list[str]:
    # Lightweight sentence splitter for demo; intentionally preserves sentence text/punctuation.
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text.strip())
    return [p.strip() for p in pieces if p.strip()]

def analyze_document(text: str) -> dict[str, Any]:
    start = time.perf_counter()
    sentences = split_sentences(text)
    results = [analyze_text(s) for s in sentences]
    counts = {label: 0 for label in ["vague","attachment","scope","pronoun"]}
    for item in results:
        seen = {d["label"] for d in item["detections"]}
        for label in counts:
            if label in seen: counts[label] += 1
    flagged = sum(bool(x["detections"]) for x in results)
    total = len(results)
    return {"sentences": results, "sentence_count": total, "flagged_count": flagged,
            "ambiguity_rate": (flagged/total*100 if total else 0.0), "type_counts": counts,
            "latency_ms": (time.perf_counter()-start)*1000, "mode": "demo_or_connected"}
