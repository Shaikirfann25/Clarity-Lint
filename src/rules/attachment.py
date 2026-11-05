"""Conservative prepositional-phrase attachment detection.

Pattern: VERB + determiner noun phrase + PREPOSITION + determiner noun
    "The admin monitors the user with the sensor."
The phrase "with the sensor" may attach to the verb (the admin uses a sensor)
or to the noun phrase (the user has a sensor).

This is deliberately narrow (no parser): it only fires on a known verb, a
determiner NP, then a preposition in `prepositions`. Default is ("with",)
because "with" is the classic instrument/accompaniment clash. You can pass
("with", "using", "in", "on") to widen it, at the cost of more false positives.
"""
import re
from typing import Dict, List, Sequence

from .common import make_detection

_VERB_BASES = (
    "monitor", "see", "observe", "inspect", "notify", "track", "check",
    "review", "scan", "watch", "open", "send", "update", "approve", "process",
    "validate", "read", "display", "handle", "report", "log", "record",
    "identify", "detect", "examine", "test", "verify", "contact", "assign",
    "inform", "guide", "help", "serve", "support", "meet", "greet", "call",
    "photograph", "film", "identify", "locate", "find", "follow", "protect",
)


def _verb_forms(bases: Sequence[str]) -> List[str]:
    forms = set()
    for v in bases:
        forms.update({v, v + "s", v + "es", v + "ed", v + "d", v + "ing"})
        if v.endswith("e"):
            forms.add(v[:-1] + "ing")
        if v.endswith("y"):
            forms.update({v[:-1] + "ies", v[:-1] + "ied"})
    forms.update({"saw", "seen", "sent", "found", "held"})
    return sorted(forms, key=len, reverse=True)


_VERBS = "|".join(_verb_forms(_VERB_BASES))
_STOP = (r"(?:and|or|but|to|in|on|at|for|by|from|of|that|which|who|when|if|"
         r"while|during|before|after|until|as|so|every|each|then|than|also)")
_WORD = r"[A-Za-z][A-Za-z-]*"

# Nouns after "with the ..." that are almost never a competing attachment site.
_EXCLUDED_PP_WORDS = {
    "following", "same", "above", "exception", "help", "aid", "assistance",
    "approval", "permission", "consent", "agreement", "knowledge",
    "consideration", "regard", "respect",
}


def _build_pattern(prepositions: Sequence[str]) -> "re.Pattern":
    preps = "|".join(re.escape(p) for p in prepositions)
    return re.compile(
        rf"\b(?P<verb>{_VERBS})\s+"
        rf"(?P<np>(?:the|a|an|each|every|all|his|her|their|its)\s+"
        rf"(?:{_WORD}\s+){{0,2}}?{_WORD})\s+"
        rf"(?P<pp>(?:{preps})\s+(?:the|a|an|his|her|their|its)\s+"
        rf"(?:(?!{_STOP}\b){_WORD}\s+)?(?!{_STOP}\b){_WORD})",
        re.IGNORECASE,
    )


_DEFAULT_PATTERN = _build_pattern(("with",))


def detect_attachment(sentence: str, prepositions: Sequence[str] = ("with",)) -> List[Dict]:
    pattern = _DEFAULT_PATTERN if tuple(prepositions) == ("with",) else _build_pattern(prepositions)
    out = []
    for m in pattern.finditer(sentence):
        pp_words = {w.lower() for w in re.findall(_WORD, m.group("pp"))}
        if pp_words & _EXCLUDED_PP_WORDS:
            continue
        reason = (
            f'The phrase "{m.group("pp")}" may attach to the action "{m.group("verb")}" '
            f'(how it is done) or to "{m.group("np")}" (describing it), '
            f"which changes who or what is involved."
        )
        out.append(make_detection("attachment", sentence, m.start("pp"), m.end("pp"), reason))
    return out
