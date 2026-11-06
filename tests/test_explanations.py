"""Tests for the explanations module (Person 4).

Covers:
  - explain() for every label, with and without span
  - rewrite() for every label
  - Determinism (same input → same output)
  - baseline JSON parsing: good JSON, fenced JSON, garbage,
    wrong label, span not in sentence
  - Meaning-preservation check (no new digits or modal verbs
    like must/shall/will beyond placeholders)
  - LLM is always mocked — no real API calls
"""
from __future__ import annotations

import json
import re

import pytest

from src.explanations.explain import explain
from src.explanations.rewrite import rewrite
from src.explanations.templates import LABELS, TEMPLATES, get_template
from src.explanations.baseline import (
    call_gemini,
    classify_sentence,
    parse_llm_response,
    predict_zero_shot,
    run_baseline,
    strip_code_fences,
    validate_prediction,
)


# ═══════════════════════════════════════════════════════════════════════════
#  TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════


class TestTemplates:
    """Every label has a well-formed template."""

    @pytest.mark.parametrize("label", LABELS)
    def test_template_exists(self, label):
        tmpl = get_template(label)
        assert "explanation" in tmpl
        assert "readings" in tmpl
        assert "rewrites" in tmpl

    def test_unknown_label_falls_back(self):
        tmpl = get_template("unknown_label_xyz")
        assert tmpl == TEMPLATES["no_ambiguity"]


# ═══════════════════════════════════════════════════════════════════════════
#  EXPLAIN
# ═══════════════════════════════════════════════════════════════════════════


EXAMPLE_DETECTIONS = {
    "vague": {
        "sentence": "The team will review the request soon.",
        "detections": [
            {"source": "rules", "label": "vague", "span": "soon",
             "confidence": None, "reason": "Vague term."},
        ],
    },
    "attachment": {
        "sentence": "The admin monitors the user with the sensor.",
        "detections": [
            {"source": "rules", "label": "attachment",
             "span": "with the sensor", "confidence": None,
             "reason": "PP attachment."},
        ],
    },
    "scope": {
        "sentence": "The system does not notify all users and administrators.",
        "detections": [
            {"source": "rules", "label": "scope", "span": "not",
             "confidence": None, "reason": "Negation scope."},
        ],
    },
    "pronoun": {
        "sentence": "Riya told Maya that she should update the report.",
        "detections": [
            {"source": "rules", "label": "pronoun", "span": "she",
             "confidence": None, "reason": "Pronoun ambiguity."},
        ],
    },
    "no_ambiguity": {
        "sentence": "The server must respond within 200 milliseconds.",
        "detections": [],
    },
}


class TestExplain:
    """explain() returns the right shape for every label."""

    @pytest.mark.parametrize("label", LABELS)
    def test_all_labels(self, label):
        case = EXAMPLE_DETECTIONS[label]
        result = explain(case["sentence"], case["detections"])

        assert isinstance(result, dict)
        assert "explanation" in result
        assert "readings" in result
        assert "rewrites" in result
        assert isinstance(result["explanation"], str)
        assert isinstance(result["readings"], list)
        assert isinstance(result["rewrites"], list)

        if label == "no_ambiguity":
            assert result["readings"] == []
            assert result["rewrites"] == []
        else:
            assert len(result["readings"]) > 0
            assert len(result["rewrites"]) > 0

    def test_empty_detections(self):
        result = explain("A clear sentence.", [])
        assert "no targeted ambiguity" in result["explanation"].lower() or \
               "no flag" in result["explanation"].lower() or \
               result["readings"] == []

    def test_unknown_label_in_detection(self):
        result = explain("Some sentence.", [
            {"source": "rules", "label": "fantasy_label", "span": "x"}
        ])
        # Should fall back to no_ambiguity
        assert result["readings"] == []

    def test_span_not_in_sentence(self):
        """If the span is not a substring, explain() should not crash."""
        result = explain("The server responds fast.", [
            {"source": "rules", "label": "vague",
             "span": "NONEXISTENT_SPAN",
             "confidence": None, "reason": "test"},
        ])
        assert isinstance(result["explanation"], str)
        # The span should be replaced with a generic placeholder
        assert "[ambiguous phrase]" in result["explanation"]

    def test_missing_span(self):
        """Detection without a span key at all."""
        result = explain("The server responds fast.", [
            {"source": "rules", "label": "vague"},
        ])
        assert isinstance(result["explanation"], str)
        assert len(result["readings"]) > 0

    def test_determinism(self):
        """Same input produces identical output."""
        case = EXAMPLE_DETECTIONS["attachment"]
        r1 = explain(case["sentence"], case["detections"])
        r2 = explain(case["sentence"], case["detections"])
        assert r1 == r2

    @pytest.mark.parametrize("sentence", [
        "The red button on the left panel opens the emergency door.",
        "The server must respond within 200 milliseconds.",
        "The platform does not store passwords in plain text.",
        "Maria submitted the assignment on Friday.",
    ])
    def test_tricky_negatives_clear_handling(self, sentence):
        """Sentences with prepositions or negations but no ambiguity flag."""
        result = explain(sentence, [])
        assert result["readings"] == []
        assert result["rewrites"] == []
        assert "no targeted ambiguity" in result["explanation"].lower() or "no flag" in result["explanation"].lower()


# ═══════════════════════════════════════════════════════════════════════════
#  REWRITE
# ═══════════════════════════════════════════════════════════════════════════


class TestRewrite:

    @pytest.mark.parametrize("label", ["vague", "attachment", "scope", "pronoun"])
    def test_ambiguity_labels_produce_rewrites(self, label):
        rw = rewrite("Example sentence with stuff.", label, "stuff")
        assert isinstance(rw, list)
        assert len(rw) > 0
        assert all(isinstance(s, str) for s in rw)

    @pytest.mark.parametrize("label", ["vague", "attachment", "scope", "pronoun"])
    def test_rewrites_offer_explicit_alternatives(self, label):
        """Rewrites must offer explicit 'If you mean' alternatives to avoid assuming intent."""
        rw = rewrite("Example sentence.", label, "phrase")
        assert any("If you mean" in option or "if you mean" in option.lower() for option in rw)

    def test_no_ambiguity_returns_empty(self):
        assert rewrite("Clear sentence.", "no_ambiguity") == []

    def test_unknown_label_returns_empty(self):
        assert rewrite("Any text.", "made_up_label") == []

    def test_span_appears_in_rewrite(self):
        rw = rewrite("Do it soon.", "vague", "soon")
        # At least one rewrite should mention the span
        assert any("soon" in r for r in rw)

    def test_meaning_preservation_no_new_digits(self):
        """Rewrites must not introduce specific numbers or modal verbs
        (must/shall/will) beyond what is in the original sentence or
        inside bracket placeholders like [N days].
        """
        sentence = "The team will review the request soon."
        rw_list = rewrite(sentence, "vague", "soon")

        # Modal verbs already in the sentence are fine
        original_modals = set(re.findall(r"\b(must|shall|will)\b",
                                         sentence, re.I))

        for rw in rw_list:
            # Strip bracketed placeholders like [N days]
            stripped = re.sub(r"\[.*?\]", "", rw)

            # No new bare digits should appear
            new_digits = re.findall(r"\b\d+\b", stripped)
            original_digits = re.findall(r"\b\d+\b", sentence)
            assert set(new_digits) <= set(original_digits), \
                f"Rewrite introduced digits: {new_digits}"

            # No new modal verbs beyond originals
            rw_modals = set(re.findall(r"\b(must|shall|will)\b",
                                       stripped, re.I))
            assert rw_modals <= original_modals, \
                f"Rewrite introduced modals: {rw_modals - original_modals}"


# ═══════════════════════════════════════════════════════════════════════════
#  BASELINE — JSON PARSING
# ═══════════════════════════════════════════════════════════════════════════


class TestBaselineParsing:

    def test_good_json(self):
        raw = '{"label": "vague", "span": "soon", "reason": "Vague term."}'
        result = parse_llm_response(raw)
        assert result is not None
        assert result["label"] == "vague"

    def test_fenced_json(self):
        raw = '```json\n{"label": "attachment", "span": "with X", "reason": "PP."}\n```'
        result = parse_llm_response(raw)
        assert result is not None
        assert result["label"] == "attachment"

    def test_fenced_no_lang(self):
        raw = '```\n{"label": "scope", "span": null, "reason": "test"}\n```'
        result = parse_llm_response(raw)
        assert result is not None
        assert result["label"] == "scope"

    def test_garbage_returns_none(self):
        assert parse_llm_response("This is not JSON at all!") is None

    def test_partial_json_in_text(self):
        raw = 'Here is my answer: {"label":"pronoun","span":"she","reason":"ref"} done.'
        result = parse_llm_response(raw)
        assert result is not None
        assert result["label"] == "pronoun"


# ═══════════════════════════════════════════════════════════════════════════
#  BASELINE — VALIDATION
# ═══════════════════════════════════════════════════════════════════════════


class TestBaselineValidation:

    def test_valid_prediction(self):
        parsed = {"label": "vague", "span": "soon", "reason": "Vague."}
        sentence = "Respond soon."
        v = validate_prediction(parsed, sentence)
        assert v["valid"] is True
        assert v["label"] == "vague"
        assert v["span"] == "soon"

    def test_wrong_label(self):
        parsed = {"label": "fantasy", "span": None, "reason": "x"}
        v = validate_prediction(parsed, "Any sentence.")
        assert v["valid"] is False
        assert v["label"] == "no_ambiguity"

    def test_span_not_in_sentence(self):
        parsed = {"label": "vague", "span": "MISSING", "reason": "x"}
        v = validate_prediction(parsed, "The system responds quickly.")
        assert v["valid"] is True
        # span should be dropped (set to None)
        assert v["span"] is None

    def test_none_parsed(self):
        v = validate_prediction(None, "Any.")
        assert v["valid"] is False
        assert v["label"] == "no_ambiguity"

    def test_null_span_string(self):
        parsed = {"label": "vague", "span": "null", "reason": "x"}
        v = validate_prediction(parsed, "Respond soon.")
        assert v["span"] is None

    def test_empty_span(self):
        parsed = {"label": "vague", "span": "", "reason": "x"}
        v = validate_prediction(parsed, "Respond soon.")
        assert v["span"] is None


# ═══════════════════════════════════════════════════════════════════════════
#  BASELINE — CLASSIFY (mocked LLM)
# ═══════════════════════════════════════════════════════════════════════════


class TestClassifySentence:
    """classify_sentence with a mocked LLM function."""

    def test_mocked_good_response(self):
        def mock_llm(sentence):
            return json.dumps({
                "label": "attachment",
                "span": "with the sensor",
                "reason": "PP attachment ambiguity.",
            })

        result = classify_sentence(
            "The admin monitors the user with the sensor.",
            llm_fn=mock_llm,
        )
        assert result["label"] == "attachment"
        assert result["span"] == "with the sensor"
        assert result["source"] == "prompt"
        assert result["valid"] is True

    def test_mocked_fenced_response(self):
        def mock_llm(sentence):
            return '```json\n{"label":"vague","span":"soon","reason":"vague"}\n```'

        result = classify_sentence("Respond soon.", llm_fn=mock_llm)
        assert result["label"] == "vague"
        assert result["valid"] is True

    def test_mocked_garbage_response(self):
        def mock_llm(sentence):
            return "I cannot help with that."

        result = classify_sentence("Any sentence.", llm_fn=mock_llm)
        assert result["label"] == "no_ambiguity"
        assert result["valid"] is False

    def test_mocked_wrong_label(self):
        def mock_llm(sentence):
            return json.dumps({"label": "invalid_type", "span": None,
                               "reason": "wrong"})

        result = classify_sentence("Any sentence.", llm_fn=mock_llm)
        assert result["label"] == "no_ambiguity"
        assert result["valid"] is False

    def test_mocked_exception(self):
        def mock_llm(sentence):
            raise ConnectionError("API down")

        result = classify_sentence("Any sentence.", llm_fn=mock_llm)
        assert result["label"] == "no_ambiguity"
        assert result["valid"] is False
        assert "API down" in result["reason"]

    def test_mocked_span_not_in_sentence(self):
        def mock_llm(sentence):
            return json.dumps({"label": "vague", "span": "WRONG",
                               "reason": "x"})

        result = classify_sentence("Respond soon.", llm_fn=mock_llm)
        assert result["valid"] is True
        assert result["span"] is None  # dropped because not a substring


# ═══════════════════════════════════════════════════════════════════════════
#  BASELINE — BATCH (mocked LLM)
# ═══════════════════════════════════════════════════════════════════════════


class TestRunBaseline:

    def test_batch_produces_correct_columns(self):
        import pandas as pd

        df = pd.DataFrame({
            "sentence_id": ["S001", "S002"],
            "text": [
                "The admin monitors the user with the sensor.",
                "The server must respond within 200 ms.",
            ],
            "label": ["attachment", "no_ambiguity"],
        })

        def mock_llm(sentence):
            if "sensor" in sentence:
                return json.dumps({"label": "attachment",
                                   "span": "with the sensor",
                                   "reason": "PP."})
            return json.dumps({"label": "no_ambiguity",
                               "span": None, "reason": "Clear."})

        result_df = run_baseline(df, llm_fn=mock_llm)

        assert list(result_df.columns) == [
            "sentence_id", "text", "gold_label", "prompt_pred",
            "span", "reason", "valid",
        ]
        assert len(result_df) == 2
        assert result_df.iloc[0]["prompt_pred"] == "attachment"
        assert result_df.iloc[1]["prompt_pred"] == "no_ambiguity"


# ═══════════════════════════════════════════════════════════════════════════
#  STRIP CODE FENCES
# ═══════════════════════════════════════════════════════════════════════════


class TestStripCodeFences:

    def test_plain_text_unchanged(self):
        assert strip_code_fences('{"a":1}') == '{"a":1}'

    def test_json_fenced(self):
        assert strip_code_fences('```json\n{"a":1}\n```') == '{"a":1}'

    def test_bare_fenced(self):
        assert strip_code_fences('```\n{"a":1}\n```') == '{"a":1}'


# ═══════════════════════════════════════════════════════════════════════════
#  PREDICT ZERO SHOT (BATCH INTERFACE & SHARED SCHEMA VERIFICATION)
# ═══════════════════════════════════════════════════════════════════════════


class TestPredictZeroShot:
    """Tests for predict_zero_shot batch prediction and integration schema."""

    def test_export_through_explanations_init(self):
        import src.explanations as pkg
        assert hasattr(pkg, "predict_zero_shot")
        assert callable(pkg.predict_zero_shot)

    def test_empty_input(self):
        assert predict_zero_shot([]) == []

    def test_batch_prediction_multiple_sentences(self):
        sentences = [
            "The supplier shall respond soon.",
            "The admin monitors the user with the sensor.",
            "The service must return HTTP 200 within 500 milliseconds.",
        ]

        def mock_llm(s: str) -> str:
            if "soon" in s:
                return json.dumps({
                    "label": "vague",
                    "span": "soon",
                    "reason": "'Soon' does not specify a measurable timeframe.",
                })
            elif "sensor" in s:
                return json.dumps({
                    "label": "attachment",
                    "span": "with the sensor",
                    "reason": "PP attachment ambiguity.",
                })
            return json.dumps({
                "label": "no_ambiguity",
                "span": None,
                "reason": "Specific measurable criteria.",
            })

        results = predict_zero_shot(sentences, llm_fn=mock_llm)

        assert isinstance(results, list)
        assert len(results) == 3

        # Sentence 1: vague
        assert results[0]["source"] == "prompt_baseline"
        assert results[0]["label"] == "vague"
        assert results[0]["span"] == "soon"
        assert results[0]["confidence"] is None
        assert "measurable timeframe" in results[0]["reason"]

        # Sentence 2: attachment
        assert results[1]["source"] == "prompt_baseline"
        assert results[1]["label"] == "attachment"
        assert results[1]["span"] == "with the sensor"
        assert results[1]["confidence"] is None

        # Sentence 3: no_ambiguity
        assert results[2]["source"] == "prompt_baseline"
        assert results[2]["label"] == "no_ambiguity"
        assert results[2]["span"] is None
        assert results[2]["confidence"] is None

    def test_verify_against_shared_integration_schema(self):
        from pathlib import Path
        schema_path = Path("docs/shared_schema.json")
        assert schema_path.exists(), "docs/shared_schema.json must exist"

        with open(schema_path, "r", encoding="utf-8") as f:
            shared_schema = json.load(f)

        # Expected prediction format from shared_schema.json
        expected_sample_pred = shared_schema["predictions"][0]
        required_keys = set(expected_sample_pred.keys())
        assert required_keys == {"source", "label", "span", "confidence", "reason"}

        sentences = [
            "The admin monitors the user with the sensor.",
            "The system is fast.",
        ]

        def mock_llm(s: str) -> str:
            if "sensor" in s:
                return json.dumps({
                    "label": "attachment",
                    "span": "with the sensor",
                    "reason": "The phrase may attach in more than one way.",
                })
            return json.dumps({
                "label": "vague",
                "span": "fast",
                "reason": "Subjective term.",
            })

        results = predict_zero_shot(sentences, llm_fn=mock_llm)
        assert len(results) == len(sentences)

        for res, sent in zip(results, sentences):
            # Check exact keys matching shared integration schema
            assert set(res.keys()) == required_keys
            assert isinstance(res["source"], str)
            assert res["label"] in LABELS
            if res["span"] is not None:
                assert isinstance(res["span"], str)
                assert res["span"] in sent
            assert res["confidence"] is None  # Prompt baseline never invents confidence
            assert isinstance(res["reason"], str)

    def test_single_string_coercion(self):
        def mock_llm(s: str) -> str:
            return json.dumps({
                "label": "vague",
                "span": "soon",
                "reason": "Vague term.",
            })

        results = predict_zero_shot("Please reply soon.", llm_fn=mock_llm)
        assert len(results) == 1
        assert results[0]["label"] == "vague"
        assert results[0]["span"] == "soon"

    def test_llm_exception_fallback(self):
        def mock_failing_llm(s: str) -> str:
            raise ConnectionError("Network unreachable")

        results = predict_zero_shot(["Any sentence here."], llm_fn=mock_failing_llm)
        assert len(results) == 1
        pred = results[0]
        assert pred["source"] == "prompt_baseline"
        assert pred["label"] == "no_ambiguity"
        assert pred["span"] is None
        assert pred["confidence"] is None
        assert "Network unreachable" in pred["reason"]

    def test_custom_source_parameter(self):
        def mock_llm(s: str) -> str:
            return json.dumps({"label": "no_ambiguity", "span": None, "reason": "Clear."})

        results = predict_zero_shot(["Clear sentence."], llm_fn=mock_llm, source="my_custom_prompt")
        assert results[0]["source"] == "my_custom_prompt"

    def test_call_gemini_missing_api_key_raises_env_error(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
            call_gemini("Any sentence")

    def test_predict_zero_shot_missing_api_key_graceful_fallback(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        # Calling without llm_fn uses call_gemini, which fails due to missing key.
        results = predict_zero_shot(["Any test sentence without key."])
        assert len(results) == 1
        assert results[0]["source"] == "prompt_baseline"
        assert results[0]["label"] == "no_ambiguity"
        assert results[0]["span"] is None
        assert results[0]["confidence"] is None
        assert "GEMINI_API_KEY" in results[0]["reason"]

    def test_predict_zero_shot_invalid_output_garbage_json(self):
        def mock_garbage(s: str) -> str:
            return "This is completely invalid and not JSON."

        results = predict_zero_shot(["Sentence."], llm_fn=mock_garbage)
        assert len(results) == 1
        assert results[0]["source"] == "prompt_baseline"
        assert results[0]["label"] == "no_ambiguity"
        assert results[0]["span"] is None
        assert "could not be validated" in results[0]["reason"]

    def test_predict_zero_shot_invalid_label(self):
        def mock_bad_label(s: str) -> str:
            return json.dumps({"label": "hallucinated_category", "span": None, "reason": "x"})

        results = predict_zero_shot(["Sentence."], llm_fn=mock_bad_label)
        assert len(results) == 1
        assert results[0]["source"] == "prompt_baseline"
        assert results[0]["label"] == "no_ambiguity"
        assert "Invalid label" in results[0]["reason"]

    def test_predict_zero_shot_hallucinated_span_stripped(self):
        def mock_bad_span(s: str) -> str:
            return json.dumps({
                "label": "vague",
                "span": "not_in_the_sentence",
                "reason": "Vague word.",
            })

        results = predict_zero_shot(["The system should respond soon."], llm_fn=mock_bad_span)
        assert len(results) == 1
        assert results[0]["label"] == "vague"
        # The hallucinated span should be stripped to None
        assert results[0]["span"] is None

    def test_predict_zero_shot_api_http_error(self):
        import requests

        def mock_http_err(s: str) -> str:
            resp = requests.Response()
            resp.status_code = 500
            resp.reason = "Internal Server Error"
            raise requests.HTTPError("500 Server Error", response=resp)

        results = predict_zero_shot(["Sentence."], llm_fn=mock_http_err)
        assert len(results) == 1
        assert results[0]["source"] == "prompt_baseline"
        assert results[0]["label"] == "no_ambiguity"
        assert results[0]["span"] is None
        assert "500 Server Error" in results[0]["reason"]

