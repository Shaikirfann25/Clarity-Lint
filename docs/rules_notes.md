# Rule-based detector notes (Person 2)

Run: `python -m pytest` (from repo root) · `python -m src.rules.detect "sentence"` · `python -m src.rules.eval_dev data/splits/dev.csv`

Entry point: `src.rules.detect.detect(sentences)` -> list of `{sentence_id, text, predictions[]}`.
Each prediction: `source="rules", label, span (exact substring), confidence=None, reason`.

## What each rule does
| Label | Module | Fires when |
|---|---|---|
| vague | vague_detector.py | a lexicon term appears (soon, as needed, appropriate, ...). Extend `DEFAULT_VAGUE_TERMS`. |
| attachment | attachment.py | known verb + "the X" + `with` + "the Y" (default preposition list is only `with`). |
| scope | scope.py | quantifier+negation; "only" before a verb with later phrases; modifier + "A and/or B"; mixed and/or. |
| pronoun | pronoun.py | a pronoun has 2+ compatible antecedent noun phrases earlier in the same sentence. |

## Known limitations (state these in the viva)
- No spaCy/parser: spaCy could not be installed in the build environment, so everything is regex + small lexicons. A trigger is evidence of *possible* ambiguity, not proof.
- Attachment: only a fixed verb list, determiner NPs, and "with"; misses bare plurals ("monitors users with sensors") and other prepositions.
- Scope: "valid data and logs the event"-style sentences can be false positives (a verb read as a noun).
- Pronoun: single sentence only; noun phrase head is a heuristic (det + 1 word); person/plural lists are small.
- Vague: lexicon only, so context-dependent vagueness is missed, and "efficient"/"robust" etc. may be fine in some documents.
- Multiple labels can be returned for one sentence; `primary_label()` collapses them using `PRIORITY` (agree this with Persons 3 and 5).

## Process
Tune only on dev data. Add a regression test in `tests/test_rules.py` for each bug fixed.
