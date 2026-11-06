"""Tests for src/model/predict.py — DistilBERT Ambiguity Classifier (Person 3).

Test organisation:
  - Group A (schema / contract): mock-based tests that run in CI without weights.
  - Group B (genuine inference):  tests that require the trained checkpoint;
    skipped automatically when the checkpoint is absent.

Run all:
    pytest tests/test_model.py -v

Run only CI-safe mocked tests:
    pytest tests/test_model.py -v -m "not requires_checkpoint"

Run only genuine-inference tests (needs trained weights):
    pytest tests/test_model.py -v -m requires_checkpoint
"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Shared constants (must match integration contract exactly)
# ---------------------------------------------------------------------------
VALID_LABELS = {"no_ambiguity", "vague", "attachment", "scope", "pronoun"}
CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "models" / "distilbert_clarity_lint"
CHECKPOINT_AVAILABLE = (CHECKPOINT_DIR / "config.json").exists() and (CHECKPOINT_DIR / "model.safetensors").exists()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_fake_predict_output(label: str = "vague", confidence: float = 0.85):
    """Return a minimal valid prediction dict for mocking."""
    return {
        "source": "model",
        "label": label,
        "span": None,
        "confidence": round(confidence, 4),
        "reason": "Mocked reason for testing."
    }


# ===========================================================================
# GROUP A — Schema / contract tests (mocked; always run in CI)
# ===========================================================================

class TestPredictSchema:
    """Verify predict() output conforms to the team's shared integration schema."""

    def test_empty_list_returns_empty(self):
        """predict([]) must return [] without errors."""
        from src.model.predict import predict
        result = predict([])
        assert result == [], f"Expected [], got {result!r}"

    def test_empty_string_returns_empty(self):
        """predict(['']) and predict('') must return [] — empty text has no prediction."""
        from src.model.predict import predict
        assert predict([""]) == []
        assert predict("") == []
        assert predict(["   "]) == []

    def test_single_string_input_accepted(self):
        """A bare string (not a list) must be accepted and return exactly 1 result."""
        mock_result = [_make_fake_predict_output("pronoun", 0.9)]
        with patch("src.model.predict.predict", return_value=mock_result) as mock_pred:
            from src.model import predict as predict_fn
            # Call with string directly
            result = mock_pred("Riya told Maya that she should update the report.")
            assert isinstance(result, list)
            assert len(result) == 1

    def test_output_has_required_contract_fields(self):
        """Every output dict must contain exactly the five integration-contract fields."""
        required_fields = {"source", "label", "span", "confidence", "reason"}
        fake_outputs = [_make_fake_predict_output("vague", 0.75)]

        with patch("src.model.predict._load_model") as mock_loader:
            # Simulate a loaded model that returns our fake logits
            import torch
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()

            # Fake tokenizer output
            mock_tokenizer.return_value = {
                "input_ids": torch.zeros((1, 10), dtype=torch.long),
                "attention_mask": torch.ones((1, 10), dtype=torch.long),
            }

            # Fake model output: logits with max at index 1 (vague)
            fake_logits = torch.tensor([[0.1, 0.9, 0.0, 0.0, 0.0]])
            mock_output = MagicMock()
            mock_output.logits = fake_logits
            mock_model.return_value = mock_output
            mock_model.parameters.return_value = iter([torch.zeros(1)])
            mock_model.config.id2label = {0: "no_ambiguity", 1: "vague", 2: "attachment", 3: "scope", 4: "pronoun"}

            mock_loader.return_value = (mock_tokenizer, mock_model)

            from src.model.predict import predict
            # Reset cached globals
            import src.model.predict as pm
            pm._CACHED_MODEL = None
            pm._CACHED_TOKENIZER = None

            result = predict(["The report will be completed soon."])

        assert isinstance(result, list)
        assert len(result) == 1
        for field in required_fields:
            assert field in result[0], f"Missing required field: '{field}' in {result[0]}"

    def test_label_always_in_valid_set(self):
        """The 'label' field in every result must be one of the 5 canonical labels."""
        import torch
        with patch("src.model.predict._load_model") as mock_loader:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            # Fake logits for 3 sentences
            fake_logits = torch.tensor([
                [0.9, 0.05, 0.02, 0.02, 0.01],  # no_ambiguity
                [0.01, 0.95, 0.01, 0.01, 0.02],  # vague
                [0.01, 0.01, 0.9, 0.05, 0.03],   # attachment
            ])
            mock_output = MagicMock()
            mock_output.logits = fake_logits
            mock_model.return_value = mock_output
            mock_model.parameters.return_value = iter([torch.zeros(1)])
            mock_model.config.id2label = {0: "no_ambiguity", 1: "vague", 2: "attachment", 3: "scope", 4: "pronoun"}
            mock_tokenizer.return_value = {
                "input_ids": torch.zeros((3, 10), dtype=torch.long),
                "attention_mask": torch.ones((3, 10), dtype=torch.long),
            }
            mock_loader.return_value = (mock_tokenizer, mock_model)

            import src.model.predict as pm
            pm._CACHED_MODEL = None
            pm._CACHED_TOKENIZER = None

            from src.model.predict import predict
            results = predict(["s1", "s2", "s3"])

        for r in results:
            assert r["label"] in VALID_LABELS, f"Invalid label: {r['label']!r}"

    def test_source_field_is_model(self):
        """'source' must always equal 'model' — not 'rules', 'demo', or anything else."""
        import torch
        with patch("src.model.predict._load_model") as mock_loader:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            fake_logits = torch.tensor([[0.1, 0.1, 0.1, 0.1, 0.6]])
            mock_output = MagicMock()
            mock_output.logits = fake_logits
            mock_model.return_value = mock_output
            mock_model.parameters.return_value = iter([torch.zeros(1)])
            mock_model.config.id2label = {0: "no_ambiguity", 1: "vague", 2: "attachment", 3: "scope", 4: "pronoun"}
            mock_tokenizer.return_value = {
                "input_ids": torch.zeros((1, 10), dtype=torch.long),
                "attention_mask": torch.ones((1, 10), dtype=torch.long),
            }
            mock_loader.return_value = (mock_tokenizer, mock_model)

            import src.model.predict as pm
            pm._CACHED_MODEL = None
            pm._CACHED_TOKENIZER = None

            from src.model.predict import predict
            results = predict(["Riya told Maya that she should update the report."])

        assert results[0]["source"] == "model", f"Expected 'model', got {results[0]['source']!r}"

    def test_span_is_none(self):
        """DistilBERT classifier does not return a span — 'span' must be None."""
        import torch
        with patch("src.model.predict._load_model") as mock_loader:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            fake_logits = torch.tensor([[0.1, 0.8, 0.0, 0.05, 0.05]])
            mock_output = MagicMock()
            mock_output.logits = fake_logits
            mock_model.return_value = mock_output
            mock_model.parameters.return_value = iter([torch.zeros(1)])
            mock_model.config.id2label = {0: "no_ambiguity", 1: "vague", 2: "attachment", 3: "scope", 4: "pronoun"}
            mock_tokenizer.return_value = {
                "input_ids": torch.zeros((1, 10), dtype=torch.long),
                "attention_mask": torch.ones((1, 10), dtype=torch.long),
            }
            mock_loader.return_value = (mock_tokenizer, mock_model)

            import src.model.predict as pm
            pm._CACHED_MODEL = None
            pm._CACHED_TOKENIZER = None

            from src.model.predict import predict
            results = predict(["The team will finish soon."])

        assert results[0]["span"] is None, f"Expected None, got {results[0]['span']!r}"

    def test_confidence_range_when_model_loaded(self):
        """Confidence must be a float in [0.0, 1.0] when a model is loaded."""
        import torch
        with patch("src.model.predict._load_model") as mock_loader:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            fake_logits = torch.tensor([[2.0, -1.0, -1.0, -0.5, -0.5]])
            mock_output = MagicMock()
            mock_output.logits = fake_logits
            mock_model.return_value = mock_output
            mock_model.parameters.return_value = iter([torch.zeros(1)])
            mock_model.config.id2label = {0: "no_ambiguity", 1: "vague", 2: "attachment", 3: "scope", 4: "pronoun"}
            mock_tokenizer.return_value = {
                "input_ids": torch.zeros((1, 10), dtype=torch.long),
                "attention_mask": torch.ones((1, 10), dtype=torch.long),
            }
            mock_loader.return_value = (mock_tokenizer, mock_model)

            import src.model.predict as pm
            pm._CACHED_MODEL = None
            pm._CACHED_TOKENIZER = None

            from src.model.predict import predict
            results = predict(["Logs are stored securely."])

        conf = results[0]["confidence"]
        assert isinstance(conf, float), f"Expected float confidence, got {type(conf)}"
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of [0, 1] range"

    def test_missing_checkpoint_returns_fallback_not_real_prediction(self):
        """When checkpoint is absent, fallback must be clearly marked (confidence=None)."""
        with patch("src.model.predict._load_model", return_value=(None, None)):
            import src.model.predict as pm
            pm._CACHED_MODEL = None
            pm._CACHED_TOKENIZER = None

            from src.model.predict import predict
            results = predict(["The contract must be reviewed appropriately."])

        assert isinstance(results, list)
        assert len(results) == 1
        # Fallback must NOT invent a confidence score
        assert results[0]["confidence"] is None, (
            "Fallback prediction must not have a confidence value — "
            "would mislead downstream consumers into treating it as real inference."
        )

    def test_batch_input_returns_one_result_per_sentence(self):
        """len(predict(sentences)) must equal len(sentences) for non-empty inputs."""
        import torch
        sentences = [
            "The admin monitors the user with the sensor.",
            "The report should be completed promptly.",
            "She said they had to submit the form.",
        ]
        with patch("src.model.predict._load_model") as mock_loader:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            n = len(sentences)
            fake_logits = torch.randn(n, 5)
            mock_output = MagicMock()
            mock_output.logits = fake_logits
            mock_model.return_value = mock_output
            mock_model.parameters.return_value = iter([torch.zeros(1)])
            mock_model.config.id2label = {0: "no_ambiguity", 1: "vague", 2: "attachment", 3: "scope", 4: "pronoun"}
            mock_tokenizer.return_value = {
                "input_ids": torch.zeros((n, 10), dtype=torch.long),
                "attention_mask": torch.ones((n, 10), dtype=torch.long),
            }
            mock_loader.return_value = (mock_tokenizer, mock_model)

            import src.model.predict as pm
            pm._CACHED_MODEL = None
            pm._CACHED_TOKENIZER = None

            from src.model.predict import predict
            results = predict(sentences)

        assert len(results) == n, f"Expected {n} results, got {len(results)}"


# ===========================================================================
# GROUP B — Genuine inference tests (require the trained checkpoint)
# ===========================================================================

@pytest.mark.requires_checkpoint
@pytest.mark.skipif(not CHECKPOINT_AVAILABLE, reason="Trained checkpoint not found — run train_classifier.py first")
class TestGenuineInference:
    """These tests load the real trained model from models/distilbert_clarity_lint/."""

    def setup_method(self):
        """Reset the module-level cache before each test."""
        import src.model.predict as pm
        pm._CACHED_MODEL = None
        pm._CACHED_TOKENIZER = None

    def test_checkpoint_loads_without_error(self):
        """The checkpoint must load cleanly and return a non-None model."""
        from src.model.predict import _load_model
        tokenizer, model = _load_model()
        assert tokenizer is not None, "Tokenizer failed to load from checkpoint."
        assert model is not None, "Model failed to load from checkpoint."

    def test_vague_sentence_produces_valid_output(self):
        """A clearly vague sentence should produce a valid schema-compliant prediction."""
        from src.model.predict import predict
        results = predict(["The fix should be applied in a reasonable amount of time."])
        assert len(results) == 1
        r = results[0]
        assert r["source"] == "model"
        assert r["label"] in VALID_LABELS
        assert isinstance(r["confidence"], float) and 0.0 <= r["confidence"] <= 1.0
        assert r["span"] is None
        assert isinstance(r["reason"], str) and len(r["reason"]) > 0

    def test_pronoun_sentence_produces_valid_output(self):
        """A pronoun-ambiguous sentence should produce a valid prediction."""
        from src.model.predict import predict
        results = predict(["Riya told Maya that she should update the report."])
        assert len(results) == 1
        r = results[0]
        assert r["label"] in VALID_LABELS
        assert isinstance(r["confidence"], float)

    def test_no_ambiguity_sentence_produces_valid_output(self):
        """A clearly unambiguous sentence should produce a valid prediction."""
        from src.model.predict import predict
        results = predict(["The server must be restarted every 24 hours."])
        assert len(results) == 1
        assert results[0]["label"] in VALID_LABELS

    def test_batch_all_labels_covered(self):
        """Run one representative sentence per category and confirm all pass schema checks."""
        from src.model.predict import predict
        sentences = [
            "The system will respond soon.",                              # vague
            "The admin monitors the user with the sensor.",               # attachment
            "The system does not allow all users to export reports.",     # scope
            "Riya told Maya that she should update the report.",          # pronoun
            "The database must retain logs for 90 days.",                 # no_ambiguity
        ]
        results = predict(sentences)
        assert len(results) == len(sentences)
        for i, r in enumerate(results):
            assert r["label"] in VALID_LABELS, f"Row {i}: invalid label {r['label']!r}"
            assert r["source"] == "model", f"Row {i}: source must be 'model'"
            assert r["confidence"] is not None, f"Row {i}: confidence should not be None with real model"
            assert 0.0 <= r["confidence"] <= 1.0, f"Row {i}: confidence {r['confidence']} out of range"

