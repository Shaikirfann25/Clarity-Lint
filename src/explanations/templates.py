"""Explanation and rewrite templates for each ambiguity label.

Each label maps to a dict with three keys:
  - explanation : a format-string that accepts {span} and {sentence}.
  - readings    : a list of format-strings (plausible alternative readings).
  - rewrites    : a list of format-strings (meaning-preserving rewrite hints).

Wording is deliberately cautious ("may be read …", "possible ambiguity")
because the tool flags candidates for human review, not definitive errors.

Rewrite rules (see docs/rewrite_policy.md):
  - Never add deadlines, numbers, actors, obligations, or conditions.
  - For vague terms use placeholders like [N days]; never pick a value.
  - If intent is unknown, present alternatives ("If you mean X: …").
"""
from __future__ import annotations

# ── Allowed labels (canonical order) ─────────────────────────────────────
LABELS: list[str] = [
    "no_ambiguity",
    "vague",
    "attachment",
    "scope",
    "pronoun",
]

# ── Templates keyed by label ─────────────────────────────────────────────
TEMPLATES: dict[str, dict[str, object]] = {
    # ── vague ─────────────────────────────────────────────────────────────
    "vague": {
        "explanation": (
            "The term \"{span}\" may lack a measurable or agreed-upon "
            "threshold in this context.  Different readers could apply "
            "different standards, making the requirement difficult to "
            "verify."
        ),
        "readings": [
            "One reader may interpret \"{span}\" as a short duration or "
            "small quantity.",
            "Another reader may interpret \"{span}\" as a longer duration "
            "or larger quantity.",
        ],
        "rewrites": [
            "If you mean a specific timeframe or deadline: replace "
            "\"{span}\" with a concrete threshold (e.g. [within N hours / by YYYY-MM-DD]).",
            "If you mean a measurable quantity or quality standard: replace "
            "\"{span}\" with explicit criteria (e.g. [minimum N units / score >= X]).",
        ],
    },

    # ── attachment ────────────────────────────────────────────────────────
    "attachment": {
        "explanation": (
            "The phrase \"{span}\" may attach to more than one part of "
            "the sentence, producing different meanings depending on "
            "which word or clause it modifies."
        ),
        "readings": [
            "If \"{span}\" modifies the action or its agent, the "
            "sentence describes how the action is performed.",
            "If \"{span}\" modifies another entity in the sentence, it "
            "describes a property or association of that entity.",
        ],
        "rewrites": [
            "If you mean the action is performed using \"{span}\": "
            "restructure the sentence so the modifier is adjacent to "
            "the verb or agent.",
            "If you mean \"{span}\" is associated with the other entity: "
            "restructure the sentence so the modifier is adjacent to "
            "that entity.",
        ],
    },

    # ── scope ─────────────────────────────────────────────────────────────
    "scope": {
        "explanation": (
            "The modifier or quantifier near \"{span}\" may apply to "
            "different parts of the sentence, changing which elements "
            "are included or excluded."
        ),
        "readings": [
            "The modifier/negation may apply to the entire coordinated "
            "group (broad scope).",
            "The modifier/negation may apply to only one element of the "
            "group (narrow scope).",
        ],
        "rewrites": [
            "If you mean the broad reading: rewrite so the modifier "
            "clearly covers all items (e.g. \"neither A nor B\").",
            "If you mean the narrow reading: rewrite so the modifier "
            "clearly applies to only the relevant item "
            "(e.g. \"A, but not B\").",
        ],
    },

    # ── pronoun ───────────────────────────────────────────────────────────
    "pronoun": {
        "explanation": (
            "The pronoun \"{span}\" may refer to more than one entity "
            "mentioned in the sentence.  Without additional context, "
            "the intended referent is unclear."
        ),
        "readings": [
            "If \"{span}\" refers to the first-mentioned entity, the "
            "sentence means one thing.",
            "If \"{span}\" refers to the second-mentioned entity, the "
            "sentence means something different.",
        ],
        "rewrites": [
            "If you mean the first-mentioned entity: replace \"{span}\" "
            "with that specific entity's name or title.",
            "If you mean the second-mentioned entity: replace \"{span}\" "
            "with that specific entity's name or title.",
        ],
    },

    # ── no_ambiguity ──────────────────────────────────────────────────────
    "no_ambiguity": {
        "explanation": (
            "No targeted ambiguity pattern was detected in this sentence.  "
            "This does not guarantee the sentence is unambiguous in every "
            "context — only that no flag was raised by the current checks."
        ),
        "readings": [],
        "rewrites": [],
    },
}


def get_template(label: str) -> dict[str, object]:
    """Return the template dict for *label*, or the no_ambiguity fallback."""
    return TEMPLATES.get(label, TEMPLATES["no_ambiguity"])

