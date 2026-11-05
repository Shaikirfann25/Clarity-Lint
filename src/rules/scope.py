"""Conservative scope-ambiguity rules. Each rule fires only when we can name
the competing readings.

1. Quantifier + negation:   "All users cannot edit the report."
2. "only" before a verb with several following phrases.
3. Modifier + coordination: "invalid passwords and usernames."
4. Mixed and/or without grouping: "admins and managers or auditors".
"""
import re
from typing import Dict, List

from .common import make_detection

# --- 1. quantifier + negation -------------------------------------------------
_NEG = (r"(?:cannot|(?:is|are|was|were|do|does|did|can|could|will|would|has|have|had)\s+not|"
        r"(?:isn|aren|wasn|weren|don|doesn|didn|couldn|won|wouldn|hasn|haven|hadn|can)['’]t)")
_QUANT_NEG = re.compile(rf"\b(?:all|every|each|both)\b[^.;:!?]{{0,80}}?\b{_NEG}", re.IGNORECASE)

# --- 2. "only" ----------------------------------------------------------------
_ONLY = re.compile(r"\bonly\b", re.IGNORECASE)
_ONLY_PREV_SKIP = {"the", "not", "and", "a", "an", "its", "their", "his", "her", "this", "that"}
_ONLY_NEXT_SKIP = {"if", "when", "once", "one", "a", "an", "single", "after", "before", "unless", "until"}
_PREPS = {"to", "by", "for", "in", "on", "at", "with", "from", "during", "after", "before", "when", "if"}

# --- 3. modifier + coordination ----------------------------------------------
_MODIFIERS = (
    "secure", "valid", "invalid", "encrypted", "authorized", "unauthorized",
    "new", "old", "large", "small", "electronic", "written", "approved",
    "registered", "local", "external", "internal", "remote", "public",
    "private", "temporary", "faulty", "damaged", "expired", "existing",
)
_NOT_NOUN_AFTER_COORD = (r"(?:the|a|an|its|their|his|her|this|that|these|those|all|any|"
                         r"each|every|no|not|to|it|they|then)")
_MOD_COORD = re.compile(
    rf"\b(?P<mod>{'|'.join(_MODIFIERS)})\s+(?P<n1>[A-Za-z][A-Za-z-]*)\s+(?P<c>and|or)\s+"
    rf"(?!{_NOT_NOUN_AFTER_COORD}\b)(?P<n2>[A-Za-z][A-Za-z-]*)\b",
    re.IGNORECASE,
)

# --- 4. mixed and/or ----------------------------------------------------------
_MIXED = re.compile(
    r"\b(?P<a>[A-Za-z][A-Za-z-]*)\s+(?P<c1>and|or)\s+(?P<b>[A-Za-z][A-Za-z-]*)\s+"
    r"(?P<c2>and|or)\s+(?P<c>[A-Za-z][A-Za-z-]*)\b",
    re.IGNORECASE,
)


def _quantifier_negation(s: str) -> List[Dict]:
    out = []
    for m in _QUANT_NEG.finditer(s):
        quant = re.match(r"\w+", m.group(0)).group(0)
        reason = (f'Negation and the quantifier "{quant}" can interact: it may mean '
                  f'"not {quant.lower()} of them" or "none of them".')
        out.append(make_detection("scope", s, m.start(), m.end(), reason))
    return out


def _only_rule(s: str) -> List[Dict]:
    out = []
    for m in _ONLY.finditer(s):
        before = s[:m.start()].split()
        if not before:                      # sentence-initial "Only admins can..."
            continue
        if before[-1].lower().strip(",;:()\"'") in _ONLY_PREV_SKIP:
            continue
        clause = re.split(r"[.;:!?]", s[m.end():], maxsplit=1)[0]
        words = re.findall(r"[A-Za-z'-]+", clause)
        if len(words) < 3 or words[0].lower() in _ONLY_NEXT_SKIP:
            continue
        if not ({w.lower() for w in words} & _PREPS):
            continue
        reason = ('"only" can limit the verb, the object, or the later phrase '
                  '(e.g. "only sends" vs "only reports" vs "only to admins"), '
                  "so the sentence can be read in more than one way.")
        out.append(make_detection("scope", s, m.start(), m.end(), reason))
    return out


def _modifier_coordination(s: str) -> List[Dict]:
    out = []
    for m in _MOD_COORD.finditer(s):
        mod, n1, c, n2 = m.group("mod"), m.group("n1"), m.group("c"), m.group("n2")
        reason = (f'"{mod}" may apply only to "{n1}" or to both "{n1}" and "{n2}" '
                  f'("{mod} {n1} {c} {n2}").')
        out.append(make_detection("scope", s, m.start(), m.end(), reason))
    return out


def _mixed_and_or(s: str) -> List[Dict]:
    out = []
    for m in _MIXED.finditer(s):
        c1, c2 = m.group("c1").lower(), m.group("c2").lower()
        if c1 == c2:
            continue
        a, b, c = m.group("a"), m.group("b"), m.group("c")
        reason = (f'Mixing "and" and "or" without grouping can mean "({a} {c1} {b}) {c2} {c}" '
                  f'or "{a} {c1} ({b} {c2} {c})".')
        out.append(make_detection("scope", s, m.start(), m.end(), reason))
    return out


def detect_scope(sentence: str) -> List[Dict]:
    return (_quantifier_negation(sentence) + _only_rule(sentence)
            + _modifier_coordination(sentence) + _mixed_and_or(sentence))
