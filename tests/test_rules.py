"""Unit test suite for Clarity Lint rule-based ambiguity detection (Person 2).

Covers:
- Schema and contract compliance (docs/shared_schema.json, docs/integration_contract.md)
- Positive, negative, and edge cases across all five categories:
  * vague
  * attachment
  * scope
  * pronoun
  * no_ambiguity
- Precedence hierarchy: attachment > pronoun > scope > vague > no_ambiguity
"""

import pytest

from src.rules import (
    detect,
    detect_attachment,
    detect_pronoun,
    detect_scope,
    detect_sentence,
    detect_vague,
    predict_label,
)

AGREED_LABELS = {"attachment", "pronoun", "scope", "vague", "no_ambiguity"}
DETECTION_KEYS = {"source", "label", "span", "confidence", "reason"}


# ==============================================================================
# 1. SCHEMA & CONTRACT COMPLIANCE TESTS
# ==============================================================================

def test_detection_schema_fields():
    """Verify that every detection dictionary contains the exact required keys."""
    results = detect(["The admin monitors the user with the sensor."])
    assert len(results) >= 1
    for d in results:
        assert set(d.keys()) == DETECTION_KEYS
        assert d["source"] == "rules"
        assert d["confidence"] is None  # Rules must NEVER invent confidence
        assert d["label"] in AGREED_LABELS
        assert isinstance(d["span"], str)
        assert isinstance(d["reason"], str)


def test_detect_empty_inputs():
    """Verify safe handling of empty inputs."""
    assert detect([]) == []
    assert detect("") == []
    assert detect("   ") == []
    assert detect_sentence("") == []


def test_detect_single_string_coercion():
    """Verify detect() accepts a single string without raising TypeError."""
    results = detect("The system should respond quickly.")
    assert isinstance(results, list)
    assert any(d["label"] == "vague" for d in results)


def test_detect_unambiguous_sentence_returns_empty_list():
    """Unflagged clear sentences must return an empty list for clean integration."""
    results = detect(["The server must respond within 200 milliseconds."])
    assert results == []


def test_detect_batch_sentences():
    """Verify batch processing of multiple sentences."""
    sentences = [
        "The system should respond quickly.",
        "Maria submitted the assignment on Friday.",
        "When Priya called Ananya she was very upset.",
    ]
    results = detect(sentences)
    labels = [d["label"] for d in results]
    assert "vague" in labels
    assert "pronoun" in labels


# ==============================================================================
# 2. VAGUE LANGUAGE TESTS
# ==============================================================================

@pytest.mark.parametrize("sentence, expected_span", [
    ("The system should respond quickly.", "quickly"),
    ("Please send the update soon.", "soon"),
    ("The project must be completed promptly.", "promptly"),
    ("The team should communicate regularly about status.", "regularly"),
    ("The migration script should complete in a reasonable amount of time.", "reasonable amount of time"),
    ("Please submit the report as soon as possible.", "as soon as possible"),
    ("Employees must complete the training in a timely manner.", "timely manner"),
    ("The configuration process should be simple to follow.", "simple to follow"),
    ("The codebase must be maintainable.", "maintainable"),
    ("The software must be robust enough to handle edge cases.", "robust enough"),
])
def test_vague_detector_positive_cases(sentence, expected_span):
    detections = detect_vague(sentence)
    assert len(detections) >= 1
    assert detections[0]["label"] == "vague"
    assert expected_span.lower() in detections[0]["span"].lower()


@pytest.mark.parametrize("sentence", [
    "The server must respond within 200 milliseconds.",
    "The service must achieve 99.9 percent uptime measured over each calendar month.",
    "The CI build must complete in under five minutes.",
    "The company was founded in 2012 and currently employs 3,200 full-time staff.",
    "Application logs must be retained for exactly 90 days.",
    "The file upload limit is 25 megabytes per individual file.",
])
def test_vague_detector_negative_cases(sentence):
    """Specific measurable numbers and thresholds must not be flagged as vague."""
    assert detect_vague(sentence) == []


# ==============================================================================
# 3. ATTACHMENT AMBIGUITY TESTS
# ==============================================================================

@pytest.mark.parametrize("sentence, expected_span", [
    ("The admin monitors the user with the sensor.", "with the sensor"),
    ("She saw the man with the telescope.", "with the telescope"),
    ("He installed the software with the missing drivers.", "with the missing drivers"),
    ("The journalist interviewed the protester standing outside the building.", "standing outside the building"),
    ("The suspect was arrested near the school wearing a dark hoodie.", "wearing a dark hoodie"),
    ("Tired after the long meeting, the project was postponed.", "Tired after the long meeting"),
    ("Having reviewed the contract, the decision was made to proceed.", "Having reviewed the contract"),
    ("Built on an unstable foundation, the architect warned about the structure.", "Built on an unstable foundation"),
    ("She submitted the sample to the lab that needed overnight analysis.", "that needed overnight analysis"),
    ("Old men and women lined up at the registration desk.", "Old men and women"),
])
def test_attachment_detector_positive_cases(sentence, expected_span):
    detections = detect_attachment(sentence)
    assert len(detections) >= 1
    assert detections[0]["label"] == "attachment"
    assert expected_span.lower() in detections[0]["span"].lower()


@pytest.mark.parametrize("sentence", [
    "Insert the USB drive into the port on the right side of the laptop.",
    "Run pip install -r requirements.txt in the project root to install all dependencies.",
    "Push all code changes to a feature branch and open a pull request targeting main.",
    "The second-floor fire exit is at the far end of the east corridor.",
    "The orange cable connects the router to the modem and must not connect to the laptop.",
])
def test_attachment_detector_negative_cases(sentence):
    """Standard, clear technical instructions must not be flagged as ambiguous attachment."""
    assert detect_attachment(sentence) == []


# ==============================================================================
# 4. SCOPE AMBIGUITY TESTS
# ==============================================================================

@pytest.mark.parametrize("sentence, expected_span", [
    ("Every student did not submit the assignment.", "Every"),
    ("All system event logs are not retained beyond the 30-day retention window.", "All"),
    ("Not all users have been successfully migrated to the new platform.", "Not all"),
    ("She does not process every request that arrives in her inbox.", "does not"),
    ("Every engineer validated the hardware or the software interface.", "Every"),
    ("Each applicant signed the consent form and the confidentiality agreement.", "Each"),
    ("Users cannot view or modify records belonging to other accounts.", "cannot"),
    ("Staff should not bypass the approval workflow or the compliance audit.", "should not"),
    ("She does not like coffee or tea.", "does not"),
    ("The team must not merge code without a passing review and sign-off.", "without"),
    ("She just added a paragraph to the introduction of the report.", "just"),
    ("He merely glanced at the agreement before appending his signature.", "merely"),
])
def test_scope_detector_positive_cases(sentence, expected_span):
    detections = detect_scope(sentence)
    assert len(detections) >= 1
    assert detections[0]["label"] == "scope"
    assert expected_span.lower() in detections[0]["span"].lower()


@pytest.mark.parametrize("sentence", [
    "The temperature sensor records a reading every five minutes and stores it in Cloud Storage.",
    "All API endpoints must require authentication using a valid JWT token.",
    "The users table has five columns: id, full_name, email, created_at, and account_status.",
    "The requirements.txt file lists all Python packages needed to run this project.",
    "Press Ctrl+S to save and Ctrl+Z to undo the last edit.",
])
def test_scope_detector_negative_cases(sentence):
    """Unambiguous scope and quantified intervals must not be flagged as ambiguous scope."""
    assert detect_scope(sentence) == []


# ==============================================================================
# 5. PRONOUN AMBIGUITY TESTS
# ==============================================================================

@pytest.mark.parametrize("sentence, expected_pronoun", [
    ("The senior engineers informed the junior engineers that they had missed an important constraint.", "they"),
    ("The HR team notified the department heads that they had to submit performance reviews.", "they"),
    ("When Priya called Ananya she was very upset.", "she"),
    ("When Raj emailed Vivek the reply he had not yet read the original message.", "he"),
    ("The project manager and the product owner disagreed and he escalated the matter.", "he"),
    ("The client spoke with the developer and then he cancelled the contract.", "he"),
    ("The administrator found the misconfiguration in the firewall rule and updated it immediately.", "it"),
    ("The developer discovered the vulnerability in the library and patched it immediately.", "it"),
    ("The database went offline unexpectedly and this blocked all active user transactions.", "this"),
    ("The professor returned the student's thesis with his detailed annotations.", "his"),
])
def test_pronoun_detector_positive_cases(sentence, expected_pronoun):
    detections = detect_pronoun(sentence)
    assert len(detections) >= 1
    assert detections[0]["label"] == "pronoun"
    assert expected_pronoun.lower() in detections[0]["span"].lower()


@pytest.mark.parametrize("sentence", [
    "Maria submitted her assignment on Friday.",
    "The temperature sensor records a reading every five minutes and stores it in Cloud Storage.",
    "Insert the USB drive into the port on the right side of the laptop.",
    "The meeting is scheduled for Monday, November 4th at 10:00 AM in Room 3B.",
    "Pull request number 312 was merged into main by Shaik on Tuesday at 11:42 AM.",
])
def test_pronoun_detector_negative_cases(sentence):
    """Sentences with single unambiguous referents must not be flagged as pronoun ambiguity."""
    assert detect_pronoun(sentence) == []


# ==============================================================================
# 6. PRECEDENCE HIERARCHY TESTS
# ==============================================================================

def test_precedence_attachment_over_vague():
    """Verify attachment takes precedence over vague modifier per Section 5 of guide."""
    # 'Old men and women' has attachment ambiguity and 'old' is slightly imprecise
    sentence = "Old men and women lined up at the registration desk."
    assert predict_label(sentence) == "attachment"

    detections = detect_sentence(sentence)
    assert len(detections) >= 1
    assert detections[0]["label"] == "attachment"


def test_precedence_attachment_over_pronoun():
    """When both attachment and pronoun triggers exist, attachment takes precedence."""
    sentence = "He interviewed the professor with the new research data."
    assert predict_label(sentence) == "attachment"


def test_precedence_scope_over_vague():
    """Universal negation with vague term should prioritize scope."""
    sentence = "Every student did not complete the simple assignment."
    assert predict_label(sentence) == "scope"


# ==============================================================================
# 7. PREDICT_LABEL COMPREHENSIVE TESTS
# ==============================================================================

@pytest.mark.parametrize("sentence, expected_label", [
    ("The system should respond quickly.", "vague"),
    ("She saw the man with the telescope.", "attachment"),
    ("Every student did not submit the assignment.", "scope"),
    ("When Priya called Ananya she was very upset.", "pronoun"),
    ("The server must respond within 200 milliseconds.", "no_ambiguity"),
    ("Maria submitted the assignment on Friday.", "no_ambiguity"),
])
def test_predict_label_all_classes(sentence, expected_label):
    assert predict_label(sentence) == expected_label

