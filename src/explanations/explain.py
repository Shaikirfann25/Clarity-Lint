"""Produce human-readable explanations, alternative readings, and rewrites.

The main entry point is :func:`explain`, which the integration pipeline
calls as::

    from src.explanations.explain import explain
    result = explain(sentence, detections)
    # result == {"explanation": str, "readings": [str], "rewrites": [str]}

This module must NOT import Streamlit.
"""
from __future__ import annotations

from typing import Any

from src.explanations.templates import LABELS, get_template
from src.explanations.rewrite import rewrite as _rewrite


def explain(sentence: str, detections: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an explanation record for *sentence* given its *detections*.

    Parameters
    ----------
    sentence : str
        The original sentence text.
    detections : list[dict]
        Each detection has at least ``label`` and optionally ``span``.
        Example::

            [{"source": "rules", "label": "attachment",
              "span": "with the sensor", "confidence": None,
              "reason": "PP may attach in more than one way."}]

    Returns
    -------
    dict
        ``{"explanation": str, "readings": [str], "rewrites": [str]}``

        - If *detections* is empty or every label is ``no_ambiguity``,
          returns the no-ambiguity explanation with empty lists.
        - ``readings`` and ``rewrites`` are always lists of strings
          (never ``None``).
    """
    # ── Pick the first non-trivial detection ──────────────────────────
    chosen = None
    for det in (detections or []):
        lbl = det.get("label", "no_ambiguity")
        if lbl in LABELS and lbl != "no_ambiguity":
            chosen = det
            break

    # ── No ambiguity detected ─────────────────────────────────────────
    if chosen is None:
        tmpl = get_template("no_ambiguity")
        return {
            "explanation": tmpl["explanation"],
            "readings": list(tmpl["readings"]),
            "rewrites": list(tmpl["rewrites"]),
        }

    label = chosen["label"]
    span = chosen.get("span")

    # Validate that the span is actually inside the sentence
    if span and span not in sentence:
        span = None

    tmpl = get_template(label)
    fill_span = span if span else "[ambiguous phrase]"

    explanation_text = tmpl["explanation"].format(span=fill_span,
                                                  sentence=sentence)

    readings = [
        r.format(span=fill_span, sentence=sentence)
        for r in tmpl.get("readings", [])
    ]

    rewrites = _rewrite(sentence, label, span)

    return {
        "explanation": explanation_text,
        "readings": readings,
        "rewrites": rewrites,
    }

