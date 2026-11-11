import pytest

from src.integration import pipeline


def test_real_rule_detector_is_connected():
    result = pipeline.analyze_text(
        "The admin monitors the user with the sensor."
    )

    assert result["component_status"]["rules"] == "available"
    assert any(
        item["label"] == "attachment"
        for item in result["detections"]
    )


def test_model_placeholder_is_not_a_real_prediction(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "_call_team_rules",
        lambda sentence: {
            "status": "available",
            "source": "team_rules",
            "predictions": [],
            "error": None,
        },
    )

    monkeypatch.setattr(
        pipeline,
        "_call_team_explanations",
        lambda sentence, detections: {
            "status": "available",
            "explanation": "No ambiguity flagged.",
            "readings": [],
            "rewrites": [],
            "error": None,
        },
    )

    monkeypatch.setattr(
        pipeline,
        "_call_team_model",
        lambda sentence: {
            "status": "unavailable",
            "prediction": None,
            "error": "Checkpoint unavailable.",
        },
    )

    result = pipeline.analyze_text("The service returns HTTP 200.")

    assert result["component_status"]["model"] == "unavailable"
    assert result["model_predictions"] == []
    assert result["mode"] == "partially_connected"


def test_multiple_rule_findings_are_preserved(monkeypatch):
    findings = [
        {
            "source": "rules",
            "label": "attachment",
            "span": "with the sensor",
            "confidence": None,
            "reason": "Attachment finding.",
        },
        {
            "source": "rules",
            "label": "pronoun",
            "span": "they",
            "confidence": None,
            "reason": "Pronoun finding.",
        },
    ]

    monkeypatch.setattr(
        pipeline,
        "_call_team_rules",
        lambda sentence: {
            "status": "available",
            "source": "team_rules",
            "predictions": findings,
            "error": None,
        },
    )

    monkeypatch.setattr(
        pipeline,
        "_call_team_explanations",
        lambda sentence, detections: {
            "status": "available",
            "explanation": "Multiple findings.",
            "readings": [],
            "rewrites": [],
            "error": None,
        },
    )

    monkeypatch.setattr(
        pipeline,
        "_call_team_model",
        lambda sentence: {
            "status": "unavailable",
            "prediction": None,
            "error": "Model unavailable.",
        },
    )

    result = pipeline.analyze_text("The admin told the user they should use the sensor.")

    assert len(result["detections"]) == 2
    assert {item["label"] for item in result["detections"]} == {
        "attachment",
        "pronoun",
    }


def test_explanation_failure_is_reported(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "_call_team_rules",
        lambda sentence: {
            "status": "available",
            "source": "team_rules",
            "predictions": [],
            "error": None,
        },
    )

    monkeypatch.setattr(
        pipeline,
        "_call_team_explanations",
        lambda sentence, detections: {
            "status": "error",
            "explanation": "Explanation engine unavailable.",
            "readings": [],
            "rewrites": [],
            "error": "Test failure.",
        },
    )

    monkeypatch.setattr(
        pipeline,
        "_call_team_model",
        lambda sentence: {
            "status": "unavailable",
            "prediction": None,
            "error": "Checkpoint unavailable.",
        },
    )

    result = pipeline.analyze_text("The service returns HTTP 200.")

    assert result["component_status"]["explanations"] == "error"
    assert result["component_errors"]["explanations"] == "Test failure."
    assert "unavailable" in result["explanation"].lower()


def test_document_reports_uniform_unavailable_model(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "_call_team_model",
        lambda sentence: {
            "status": "unavailable",
            "prediction": None,
            "error": "Checkpoint unavailable.",
        },
    )

    result = pipeline.analyze_document(
        "The supplier shall respond soon. "
        "The service returns HTTP 200."
    )

    assert result["sentence_count"] == 2
    assert result["component_status"]["model"] == "unavailable"
    assert result["component_status"]["rules"] == "available"
    assert result["component_status"]["explanations"] == "available"
