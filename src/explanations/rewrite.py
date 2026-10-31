"""Generate meaning-preserving rewrite suggestions for a flagged sentence.

Rewrites follow the policy in docs/rewrite_policy.md:
  - Never add deadlines, numbers, actors, obligations, or conditions.
  - For vague terms use placeholders like [N days]; never pick a value.
  - If intent is unknown, present alternatives ("If you mean X: …").
  - Wording is cautious — outputs are suggestions needing human review.

This module must NOT import Streamlit.
"""
from __future__ import annotations

from src.explanations.templates import LABELS, get_template


def rewrite(sentence: str, label: str, span: str | None = None) -> list[str]:
    """Return a list of rewrite suggestions for *sentence*.

    Parameters
    ----------
    sentence : str
        The original sentence text.
    label : str
        One of the five canonical labels.
    span : str or None
        The ambiguous substring (exact match inside *sentence*), or None.

    Returns
    -------
    list[str]
        Rewrite suggestions.  Empty list when no rewrite applies
        (e.g. ``no_ambiguity`` or unknown label).
    """
    # Nothing to rewrite for clear sentences or unknown labels
    if label not in LABELS or label == "no_ambiguity":
        return []

    template = get_template(label)
    raw_rewrites: list[str] = list(template.get("rewrites", []))

    # If we have no templates for some reason, return empty
    if not raw_rewrites:
        return []

    # Use the span in the template if available; otherwise use a
    # generic placeholder so the output is still useful.
    fill_span = span if span else "[ambiguous phrase]"

    return [r.format(span=fill_span, sentence=sentence) for r in raw_rewrites]

