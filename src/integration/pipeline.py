"""Transparent integration adapters for Clarity Lint.

Real component outputs are kept separate from illustrative demo output.
Unavailable components are reported explicitly; no silent fallback is used.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any


LABELS = {"no_ambiguity", "vague", "attachment", "scope", "pronoun"}
DEMO_ENABLED = os.getenv("CLARITY_LINT_DEMO_MODE", "").strip().lower() in {
    "1", "true", "yes", "on"
}

VAGUE_TERMS = [
    "soon", "appropriate", "regularly", "as needed",
    "reasonable", "promptly", "adequate", "timely"
]


def demo_mode_label() -> str:
    return "DEMO / illustrative fallback (explicitly enabled only)"


def _demo_detect(sentence: str) -> list[dict[str, Any]]:
    found = []

    for term in VAGUE_TERMS:
        match = re.search(r"\b" + re.escape(term) + r"\b", sentence, re.I)
        if match:
            found.append({
                "source": "demo_rules",
                "label": "vague",
                "span": match.group(0),
                "confidence": None,
                "reason": "Illustrative heuristic: this term may lack a measurable threshold."
            })
            break

    return found


def _demo_explain(sentence: str, detections: list[dict[str, Any]]):
    if not detections:
        return (
            "No illustrative demo pattern flagged this sentence. "
            "This does not prove that it is unambiguous.",
            [],
            []
        )

    return (
        "Illustrative explanation only. Review the flagged phrase in context.",
        ["The phrase may have more than one interpretation."],
        ["Rewrite the sentence to state the intended meaning explicitly."]
    )


def _normalise_findings(rule_records: Any) -> list[dict[str, Any]]:
    """Adapt the team's nested predictions schema to dashboard findings."""
    if not isinstance(rule_records, list):
        raise ValueError("Rule detector did not return a list.")

    findings = []

    for record in rule_records:
        if not isinstance(record, dict):
            continue

        nested = record.get("predictions")

        if isinstance(nested, list):
            candidates = nested
        elif record.get("label") in LABELS and record.get("label") != "no_ambiguity":
            candidates = [record]
        else:
            candidates = []

        for item in candidates:
            if not isinstance(item, dict):
                continue

            label = item.get("label")
            if label not in LABELS or label == "no_ambiguity":
                continue

            findings.append({
                "source": item.get("source", "rules"),
                "label": label,
                "span": item.get("span"),
                "confidence": item.get("confidence"),
                "reason": item.get("reason") or "Possible ambiguity detected; review in context."
            })

    return findings


def _call_team_rules(sentence: str) -> dict[str, Any]:
    try:
        from src.rules.detect import detect

        result = detect([sentence])
        findings = _normalise_findings(result)

        return {
            "status": "available",
            "source": "team_rules",
            "predictions": findings,
            "error": None
        }
    except Exception as exc:
        return {
            "status": "error",
            "source": "team_rules",
            "predictions": [],
            "error": f"{type(exc).__name__}: {exc}"
        }


def _call_team_model(sentence: str) -> dict[str, Any]:
    try:
        from src.model.predict import predict

        result = predict([sentence])

        if not isinstance(result, list) or len(result) != 1:
            return {
                "status": "invalid_output",
                "prediction": None,
                "error": "Model adapter did not return exactly one prediction."
            }

        prediction = result[0]

        if not isinstance(prediction, dict):
            return {
                "status": "invalid_output",
                "prediction": None,
                "error": "Model prediction is not a dictionary."
            }

        label = prediction.get("label")
        confidence = prediction.get("confidence")

        if label not in LABELS or not isinstance(confidence, (int, float)):
            return {
                "status": "unavailable",
                "prediction": None,
                "error": prediction.get("reason") or
                         "Model returned a placeholder or invalid prediction."
            }

        if not 0.0 <= float(confidence) <= 1.0:
            return {
                "status": "invalid_output",
                "prediction": None,
                "error": "Model confidence is outside the range 0 to 1."
            }

        return {
            "status": "available",
            "prediction": {
                "source": "model",
                "label": label,
                "span": prediction.get("span"),
                "confidence": float(confidence),
                "reason": prediction.get("reason", "")
            },
            "error": None
        }

    except Exception as exc:
        return {
            "status": "error",
            "prediction": None,
            "error": f"{type(exc).__name__}: {exc}"
        }


def _call_team_explanations(
    sentence: str,
    detections: list[dict[str, Any]]
) -> dict[str, Any]:
    try:
        from src.explanations.explain import explain

        result = explain(sentence, detections)

        if not isinstance(result, dict):
            raise ValueError("Explanation engine did not return a dictionary.")

        explanation = result.get("explanation")
        readings = result.get("readings", [])
        rewrites = result.get("rewrites", [])

        if not isinstance(explanation, str):
            raise ValueError("Explanation field must be a string.")

        if not isinstance(readings, list) or not all(
            isinstance(item, str) for item in readings
        ):
            raise ValueError("Readings must be a list of strings.")

        if not isinstance(rewrites, list) or not all(
            isinstance(item, str) for item in rewrites
        ):
            raise ValueError("Rewrites must be a list of strings.")

        return {
            "status": "available",
            "explanation": explanation,
            "readings": readings,
            "rewrites": rewrites,
            "error": None
        }

    except Exception as exc:
        return {
            "status": "error",
            "explanation": "Explanation engine unavailable. Review the detector evidence directly.",
            "readings": [],
            "rewrites": [],
            "error": f"{type(exc).__name__}: {exc}"
        }


def analyze_text(sentence: str) -> dict[str, Any]:
    if not isinstance(sentence, str):
        raise TypeError("sentence must be a string.")

    if not sentence.strip():
        raise ValueError("sentence must not be empty.")

    start = time.perf_counter()

    rule_result = _call_team_rules(sentence)
    detections = rule_result["predictions"]

    if rule_result["status"] != "available" and DEMO_ENABLED:
        detections = _demo_detect(sentence)
        for finding in detections:
            finding["source"] = "demo_rules"

        rule_status = "demo"
    else:
        rule_status = rule_result["status"]

    explanation_result = _call_team_explanations(sentence, detections)

    if explanation_result["status"] != "available" and DEMO_ENABLED:
        explanation, readings, rewrites = _demo_explain(sentence, detections)
        explanation_status = "demo"
    else:
        explanation = explanation_result["explanation"]
        readings = explanation_result["readings"]
        rewrites = explanation_result["rewrites"]
        explanation_status = explanation_result["status"]

    model_result = _call_team_model(sentence)

    model_predictions = (
        [model_result["prediction"]]
        if model_result["status"] == "available"
        else []
    )

    statuses = {
        "rules": rule_status,
        "model": model_result["status"],
        "explanations": explanation_status
    }

    if all(value in {"available"} for value in statuses.values()):
        mode = "fully_connected"
    elif any(value == "available" for value in statuses.values()):
        mode = "partially_connected"
    elif any(value == "demo" for value in statuses.values()):
        mode = "demo"
    else:
        mode = "unavailable"

    return {
        "sentence_id": None,
        "text": sentence,
        "detections": detections,
        "model_predictions": model_predictions,
        "explanation": explanation,
        "readings": readings,
        "rewrites": rewrites,
        "mode": mode,
        "component_status": statuses,
        "component_errors": {
            "rules": rule_result.get("error"),
            "model": model_result.get("error"),
            "explanations": explanation_result.get("error")
        },
        "latency_ms": (time.perf_counter() - start) * 1000
    }


def split_sentences(text: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text.strip())
    return [piece.strip() for piece in pieces if piece.strip()]


def analyze_document(text: str) -> dict[str, Any]:
    start = time.perf_counter()

    sentences = split_sentences(text)
    results = [analyze_text(sentence) for sentence in sentences]

    counts = {
        "vague": 0,
        "attachment": 0,
        "scope": 0,
        "pronoun": 0
    }

    for item in results:
        seen = {finding["label"] for finding in item["detections"]}
        for label in counts:
            if label in seen:
                counts[label] += 1

    flagged = sum(bool(item["detections"]) for item in results)
    total = len(results)

    component_status = {}

    for component in ("rules", "model", "explanations"):
        values = {item["component_status"][component] for item in results}

        if not values:
            component_status[component] = "not_run"
        elif values == {"available"}:
            component_status[component] = "available"
        elif values == {"demo"}:
            component_status[component] = "demo"
        elif len(values) == 1:
            component_status[component] = next(iter(values))
        elif values.issubset({"available", "demo"}):
            component_status[component] = "partially_demo"
        else:
            component_status[component] = "mixed"

    modes = {item["mode"] for item in results}

    if not modes:
        mode = "not_run"
    elif len(modes) == 1:
        mode = next(iter(modes))
    else:
        mode = "mixed"

    return {
        "sentences": results,
        "sentence_count": total,
        "flagged_count": flagged,
        "ambiguity_rate": (flagged / total * 100) if total else 0.0,
        "type_counts": counts,
        "component_status": component_status,
        "latency_ms": (time.perf_counter() - start) * 1000,
        "mode": mode
    }
