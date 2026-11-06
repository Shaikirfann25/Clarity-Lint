"""Inference adapter for DistilBERT Ambiguity Classifier (Person 3).

Exposes predict(sentences) following the team's shared contract:
  - Input: list of string sentences (or a single string)
  - Output: list of prediction dictionaries matching the integration schema:
      [{
          "source": "model",
          "label": "<one of the 5 labels>",
          "span": None,
          "confidence": float (softmax probability),
          "reason": "<descriptive reason>"
      }]
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Union

LABEL_MAP = {
    0: "no_ambiguity",
    1: "vague",
    2: "attachment",
    3: "scope",
    4: "pronoun"
}

LABEL_REASONS = {
    "no_ambiguity": "No prominent grammatical or lexical ambiguity detected by DistilBERT.",
    "vague": "Model detected vague terminology lacking measurable criteria.",
    "attachment": "Model detected potential attachment ambiguity in phrase structure.",
    "scope": "Model detected competing modifier or logical scope readings.",
    "pronoun": "Model detected ambiguous pronoun or unclear referent."
}

# Default checkpoint path relative to project root
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "distilbert_clarity_lint"

# Lazy-loaded cache
_CACHED_TOKENIZER = None
_CACHED_MODEL = None


def _load_model(model_dir: Path | str | None = None):
    global _CACHED_TOKENIZER, _CACHED_MODEL
    if _CACHED_MODEL is not None and _CACHED_TOKENIZER is not None:
        return _CACHED_TOKENIZER, _CACHED_MODEL

    path = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
    if not (path.exists() and (path / "config.json").exists()):
        return None, None

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        device = "cuda" if torch.cuda.is_available() else "cpu"
        tokenizer = AutoTokenizer.from_pretrained(str(path))
        model = AutoModelForSequenceClassification.from_pretrained(str(path))
        model.to(device)
        model.eval()

        _CACHED_TOKENIZER = tokenizer
        _CACHED_MODEL = model
        return tokenizer, model
    except Exception as e:
        print(f"[DistilBERT] Warning: Failed to load checkpoint from {path}: {e}")
        return None, None


def predict(sentences: Union[List[str], str], model_dir: Path | str | None = None) -> List[dict[str, Any]]:
    """Predict ambiguity labels for a batch of sentences using the fine-tuned DistilBERT model.

    Args:
        sentences: A list of sentence strings (or a single string).
        model_dir: Optional custom model checkpoint directory.

    Returns:
        List of dicts formatted per team integration contract.
    """
    if isinstance(sentences, str):
        sentences = [sentences]

    # Filter out empty / whitespace-only strings
    sentences = [s for s in sentences if isinstance(s, str) and s.strip()]

    if not sentences:
        return []

    tokenizer, model = _load_model(model_dir)

    # Fallback if model is not yet fine-tuned/saved
    if model is None or tokenizer is None:
        return [
            {
                "source": "model",
                "label": "no_ambiguity",
                "span": None,
                "confidence": None,
                "reason": "Model checkpoint not yet loaded; train_classifier.py awaiting dataset from Person 1."
            }
            for _ in sentences
        ]

    import torch

    device = next(model.parameters()).device
    encoded = tokenizer(
        sentences,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        outputs = model(**encoded)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        confidences, preds = torch.max(probs, dim=-1)

    results = []
    id2label = getattr(model.config, "id2label", None) or LABEL_MAP

    for pred_idx, conf in zip(preds.cpu().tolist(), confidences.cpu().tolist()):
        label = id2label.get(pred_idx, LABEL_MAP.get(pred_idx, "no_ambiguity"))
        results.append({
            "source": "model",
            "label": label,
            "span": None,
            "confidence": round(float(conf), 4),
            "reason": LABEL_REASONS.get(label, "Transformer-based sequence classification prediction.")
        })

    return results


if __name__ == "__main__":
    test_sentences = [
        "The admin monitors the user with the sensor.",
        "The team will review the request soon.",
        "The system does not allow all users to export reports.",
        "Riya told Maya that she should update the report.",
        "The database will store records permanently."
    ]
    print(f"Testing inference with {len(test_sentences)} sample sentences:")
    res = predict(test_sentences)
    for s, r in zip(test_sentences, res):
        print(f"  Sentence: {s}")
        print(f"  Prediction: {r}\n")

