"""Unit tests for the rule-based detectors (Person 2).

Every sentence here was hand-checked. Positives assert label AND exact span;
negatives assert that the label is NOT produced.
Add a regression test below for every bug you fix.
"""
import pytest

from src.rules.attachment import detect_attachment
from src.rules.common import LABELS
from src.rules.detect import detect, detect_sentence, primary_label
from src.rules.pronoun import detect_pronoun
from src.rules.scope import detect_scope
from src.rules.vague_detector import detect_vague


def spans(preds):
    return [p["span"] for p in preds]


# ---------------------------------------------------------------- vague ------
@pytest.mark.parametrize("sentence, expected", [
    ("The system shall respond soon after login.", ["soon"]),
    ("Backups run regularly.", ["regularly"]),
    ("The user may be notified as needed.", ["as needed"]),
    ("Appropriate measures shall be taken.", ["Appropriate"]),
    ("Complete the task as soon as possible.", ["as soon as possible"]),  # no extra 'soon'
])
def test_vague_positive(sentence, expected):
    assert spans(detect_vague(sentence)) == expected


@pytest.mark.parametrize("sentence", [
    "The system shall respond within 2 seconds.",
    "Backups run every 24 hours.",
    "The report is sent to the manager.",
])
def test_vague_negative(sentence):
    assert detect_vague(sentence) == []


def test_vague_custom_lexicon():
    assert spans(detect_vague("Respond with low latency.", lexicon=["low latency"])) == ["low latency"]
    assert detect_vague("Respond soon.", lexicon=[]) == []


# ----------------------------------------------------------- attachment ------
def test_attachment_doc_example():
    preds = detect_attachment("The admin monitors the user with the sensor.")
    assert spans(preds) == ["with the sensor"]
    assert preds[0]["label"] == "attachment"


def test_attachment_other_positive():
    assert spans(detect_attachment("The doctor examined the patient with the stethoscope.")) == [
        "with the stethoscope"]


@pytest.mark.parametrize("sentence", [
    "The admin uses the sensor to monitor the user.",
    "The admin monitors the user.",
    "The system shall comply with the following requirements.",
    "The system updates the record with the following values.",
])
def test_attachment_negative(sentence):
    assert detect_attachment(sentence) == []


def test_attachment_prepositions_configurable():
    s = "The system updates the record using the API."
    assert detect_attachment(s) == []
    assert spans(detect_attachment(s, prepositions=("with", "using"))) == ["using the API"]


# ---------------------------------------------------------------- scope ------
@pytest.mark.parametrize("sentence, expected", [
    ("All users cannot edit the report.", ["All users cannot"]),
    ("Each request is not logged.", ["Each request is not"]),
    ("The system only sends reports to managers.", ["only"]),
    ("The system rejects invalid passwords and usernames.", ["invalid passwords and usernames"]),
    ("Admins and managers or auditors can view logs.", ["Admins and managers or auditors"]),
])
def test_scope_positive(sentence, expected):
    preds = detect_scope(sentence)
    assert spans(preds) == expected
    assert all(p["label"] == "scope" for p in preds)


@pytest.mark.parametrize("sentence", [
    "The system shall not store passwords.",
    "Users must not share passwords.",
    "Only managers can approve requests.",
    "The system sends reports only to managers.",
    "Users and/or admins can view logs.",
    "The system sends the report to the manager and the admin.",
    "All users are required to log in.",
])
def test_scope_negative(sentence):
    assert detect_scope(sentence) == []


# -------------------------------------------------------------- pronoun ------
@pytest.mark.parametrize("sentence, pronoun", [
    ("The server sends the request to the client when it is ready.", "it"),
    ("The admin notifies the user when he logs in.", "he"),
    ("The developers reviewed the patches and they were merged.", "they"),
])
def test_pronoun_positive(sentence, pronoun):
    preds = detect_pronoun(sentence)
    assert spans(preds) == [pronoun]
    assert preds[0]["label"] == "pronoun"


@pytest.mark.parametrize("sentence", [
    "The user clicks the button and it opens the dialog.",   # one non-person candidate
    "It is important to log every request.",                  # expletive 'it'
    "The manager approved the report because he trusted the team.",  # one person candidate
    "The system stores the data.",                            # no pronoun
])
def test_pronoun_negative(sentence):
    assert detect_pronoun(sentence) == []


# ---------------------------------------------------- combined / schema ------
def test_detect_schema_and_exact_spans():
    sentences = [
        "The admin monitors the user with the sensor soon.",
        "The system shall respond within 2 seconds.",
    ]
    records = detect(sentences)
    assert [r["sentence_id"] for r in records] == ["S001", "S002"]
    for r in records:
        for p in r["predictions"]:
            assert p["source"] == "rules"
            assert p["confidence"] is None
            assert p["label"] in LABELS
            assert p["span"] in r["text"]            # exact substring
            assert isinstance(p["reason"], str) and p["reason"]
    assert [p["label"] for p in records[0]["predictions"]] == ["attachment", "vague"]
    assert records[1]["predictions"] == []


def test_detect_is_deterministic():
    s = ["The server sends the request to the client when it is ready as needed."] * 3
    assert detect(s) == detect(s)
    recs = detect(s)
    assert recs[0]["predictions"] == recs[1]["predictions"]
    assert {p["label"] for p in recs[0]["predictions"]} == {"pronoun", "vague"}


def test_detect_accepts_dicts_and_passes_ids():
    recs = detect([{"sentence_id": "X9", "text": "Respond soon.", "gold_label": "vague"}])
    assert recs[0]["sentence_id"] == "X9" and recs[0]["gold_label"] == "vague"


def test_primary_label():
    rec = detect(["The admin monitors the user with the sensor soon."])[0]
    assert primary_label(rec) == "attachment"
    assert primary_label(rec, priority=("vague", "attachment")) == "vague"
    assert primary_label(detect(["The system stores the data."])[0]) == "no_ambiguity"


def test_enabled_rules_filter():
    preds = detect_sentence("The admin monitors the user with the sensor soon.", enabled=["vague"])
    assert [p["label"] for p in preds] == ["vague"]


def test_empty_and_bad_input():
    assert detect([""])[0]["predictions"] == []
    with pytest.raises(ValueError):
        detect([{"sentence_id": "S1"}])
