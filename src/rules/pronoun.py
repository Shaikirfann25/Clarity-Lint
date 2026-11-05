"""Pronoun/reference ambiguity: flag a pronoun only when it has TWO OR MORE
plausible antecedents earlier in the same sentence.

Candidate antecedents are determiner noun phrases ("the server", "a request").
Compatibility is a cheap heuristic:
  it / its            -> singular, non-person nouns
  they / them / their -> plural-looking nouns (ending in -s)
  he/him/his/she/her  -> person/role nouns (user, admin, manager, ...)

Limits: single-sentence only (no cross-sentence antecedents), no parser, so
compound nouns and unusual head nouns can be mis-read. Not every pronoun is
flagged: one candidate, or none, means no flag.
"""
import re
from typing import Dict, List

from .common import make_detection

_PRONOUN = re.compile(r"\b(?:it|its|they|them|their|theirs|he|him|his|she|her)\b", re.IGNORECASE)
_NP = re.compile(r"\b(?:the|a|an|each|every)\s+([A-Za-z][A-Za-z-]*)(?:\s+([A-Za-z][A-Za-z-]*))?",
                 re.IGNORECASE)

_PERSON = {
    "user", "users", "admin", "admins", "administrator", "administrators",
    "manager", "managers", "customer", "customers", "client", "clients",
    "employee", "employees", "developer", "developers", "tester", "testers",
    "operator", "operators", "supplier", "suppliers", "vendor", "vendors",
    "buyer", "buyers", "seller", "sellers", "tenant", "tenants", "landlord",
    "contractor", "contractors", "party", "parties", "doctor", "doctors",
    "patient", "patients", "officer", "officers", "owner", "owners",
    "teacher", "teachers", "student", "students", "engineer", "engineers",
    "auditor", "auditors", "reviewer", "reviewers", "member", "members",
}
_ADJ_SKIP = {
    "new", "old", "same", "other", "first", "last", "next", "previous",
    "current", "valid", "invalid", "active", "inactive", "main", "primary",
    "secondary", "additional", "relevant", "applicable", "original",
    "existing", "final", "initial", "second", "third", "large", "small",
    "high", "low", "available", "authorized", "unauthorized", "registered",
    "secure", "encrypted", "senior", "junior", "external", "internal",
}
_NOT_NOUN = {"following", "above", "below", "only", "least", "most", "such",
             "same", "other", "first", "last", "next", "previous"}

_EXPLETIVE = re.compile(
    r"^\s+(?:is|was|will be|shall be|should be|may be|might be|must be|has been)\s+"
    r"(?:(?:not|also|very|highly)\s+)?"
    r"(?:necessary|important|possible|impossible|required|recommended|essential|clear|"
    r"likely|unlikely|mandatory|advisable|acceptable|difficult|easy|critical|expected|"
    r"assumed|understood|noted|determined)\b"
    r"|^\s+(?:seems|appears|rains)\b",
    re.IGNORECASE,
)


def _is_plural(word: str) -> bool:
    w = word.lower()
    return w.endswith("s") and not w.endswith(("ss", "us", "is"))


def _candidates(before: str) -> List[str]:
    heads = []
    for m in _NP.finditer(before):
        first, second = m.group(1), m.group(2)
        word = first
        if first.lower() in _ADJ_SKIP and second:
            word = second
        if word.lower() in _NOT_NOUN or word.lower() in _ADJ_SKIP:
            continue
        if word.lower() not in [h.lower() for h in heads]:
            heads.append(word)
    return heads


def _compatible(pronoun: str, heads: List[str]) -> List[str]:
    p = pronoun.lower()
    if p in {"it", "its"}:
        return [h for h in heads if not _is_plural(h) and h.lower() not in _PERSON]
    if p in {"they", "them", "their", "theirs"}:
        return [h for h in heads if _is_plural(h)]
    return [h for h in heads if h.lower() in _PERSON]


def detect_pronoun(sentence: str) -> List[Dict]:
    out = []
    for m in _PRONOUN.finditer(sentence):
        pron = m.group(0)
        if pron.lower() == "it" and _EXPLETIVE.search(sentence[m.end():]):
            continue
        cands = _compatible(pron, _candidates(sentence[:m.start()]))
        if len(cands) < 2:
            continue
        listed = ", ".join(f'"{c}"' for c in cands[:-1]) + f' or "{cands[-1]}"'
        reason = f'The pronoun "{pron}" could refer to {listed}.'
        out.append(make_detection("pronoun", sentence, m.start(), m.end(), reason))
    return out
