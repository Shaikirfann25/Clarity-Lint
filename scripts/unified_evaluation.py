"""Evidence-aware comparative evaluation for Clarity Lint.

Uses the frozen test split without tuning.
Does not overwrite the original benchmark files.
Rules are freshly evaluated.
Gemini uses only valid, aligned cached predictions.
DistilBERT cached predictions are preserved but not scored because
the current checkpoint weights are unavailable.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LABELS = ["no_ambiguity", "vague", "attachment", "scope", "pronoun"]

TEST_PATH = ROOT / "data" / "splits" / "test.csv"
GEMINI_PATH = ROOT / "outputs" / "prompt_baseline_test_predictions.csv"
MODEL_PATH = ROOT / "outputs" / "model_test_predictions.csv"

OUTPUT_CSV = ROOT / "outputs" / "integration_comparative_predictions.csv"
OUTPUT_JSON = ROOT / "outputs" / "integration_comparative_report.json"


def validate_unique_ids(df: pd.DataFrame, name: str) -> None:
    if "sentence_id" not in df.columns:
        raise ValueError(f"{name} is missing sentence_id.")

    if df["sentence_id"].isna().any():
        raise ValueError(f"{name} contains missing sentence IDs.")

    if df["sentence_id"].duplicated().any():
        raise ValueError(f"{name} contains duplicate sentence IDs.")


def validate_alignment(reference: pd.DataFrame, candidate: pd.DataFrame,
                       name: str, label_column: str) -> None:
    validate_unique_ids(reference, "Frozen test set")
    validate_unique_ids(candidate, name)

    if set(reference["sentence_id"]) != set(candidate["sentence_id"]):
        raise ValueError(f"{name} IDs do not exactly match the frozen test set.")

    aligned = candidate.set_index("sentence_id").reindex(
        reference["sentence_id"]
    )

    expected_text = reference["text"].astype(str).tolist()
    actual_text = aligned["text"].astype(str).tolist()

    if expected_text != actual_text:
        raise ValueError(f"{name} text does not match the frozen test set.")

    expected_labels = reference["label"].astype(str).tolist()
    actual_labels = aligned[label_column].astype(str).tolist()

    if expected_labels != actual_labels:
        raise ValueError(f"{name} gold labels do not match the frozen test set.")


def calculate_metrics(y_true, y_pred):
    if len(y_true) == 0 or len(y_true) != len(y_pred):
        raise ValueError("Metric inputs must have equal, non-zero lengths.")

    invalid = set(y_pred) - set(LABELS)
    if invalid:
        raise ValueError(f"Invalid prediction labels: {sorted(invalid)}")

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=LABELS,
        average=None,
        zero_division=0,
    )

    macro = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=LABELS,
        average="macro",
        zero_division=0,
    )

    weighted = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=LABELS,
        average="weighted",
        zero_division=0,
    )

    return {
        "n_examples": len(y_true),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_precision": round(float(macro[0]), 4),
        "macro_recall": round(float(macro[1]), 4),
        "macro_f1": round(float(macro[2]), 4),
        "weighted_f1": round(float(weighted[2]), 4),
        "per_class": {
            label: {
                "precision": round(float(precision[i]), 4),
                "recall": round(float(recall[i]), 4),
                "f1": round(float(f1[i]), 4),
                "support": int(support[i]),
            }
            for i, label in enumerate(LABELS)
        },
        "confusion_matrix": {
            "labels": LABELS,
            "matrix": confusion_matrix(
                y_true, y_pred, labels=LABELS
            ).tolist(),
        },
    }


def main():
    if not TEST_PATH.exists():
        raise FileNotFoundError(TEST_PATH)

    if not GEMINI_PATH.exists():
        raise FileNotFoundError(GEMINI_PATH)

    test = pd.read_csv(TEST_PATH)
    required = {"sentence_id", "text", "label"}

    if not required.issubset(test.columns):
        raise ValueError("Frozen test set is missing required columns.")

    validate_unique_ids(test, "Frozen test set")

    if test[list(required)].isna().any().any():
        raise ValueError("Frozen test set contains missing required values.")

    if not set(test["label"]).issubset(set(LABELS)):
        raise ValueError("Frozen test set contains non-canonical labels.")

    print(f"Frozen test set: {len(test)} examples")

    # Fresh rule-based predictions.
    from src.rules.detect import predict_label

    print("Running genuine Rule-Based Detector...")
    start = time.perf_counter()
    rules_predictions = [
        predict_label(text) for text in test["text"].astype(str).tolist()
    ]
    rules_runtime_ms = (time.perf_counter() - start) * 1000

    if not set(rules_predictions).issubset(set(LABELS)):
        raise ValueError("Rule detector returned an invalid label.")

    # Cached Gemini predictions with validity preserved.
    print("Loading and validating cached Gemini predictions...")
    gemini = pd.read_csv(GEMINI_PATH)

    required_gemini = {
        "sentence_id", "text", "gold_label", "prompt_pred", "valid"
    }
    if not required_gemini.issubset(gemini.columns):
        raise ValueError("Gemini prediction file is missing required columns.")

    validate_alignment(test, gemini, "Gemini predictions", "gold_label")

    valid_values = gemini["valid"].astype(str).str.strip().str.lower()
    valid_mask = valid_values.isin(["true", "1", "yes"])

    invalid_count = int((~valid_mask).sum())
    gemini_valid = gemini.loc[valid_mask].copy()

    if not set(gemini_valid["prompt_pred"]).issubset(set(LABELS)):
        raise ValueError("Valid Gemini rows contain invalid prediction labels.")

    if gemini_valid["prompt_pred"].isna().any():
        raise ValueError("Valid Gemini rows contain missing predictions.")

    # Build the combined prediction file. Failed Gemini rows remain blank.
    result = test[["sentence_id", "text", "label"]].copy()
    result = result.rename(columns={"label": "gold_label"})
    result["rules_pred"] = rules_predictions
    result["gemini_pred"] = pd.NA
    result["gemini_valid"] = False
    result["distilbert_cached_pred"] = pd.NA
    result["distilbert_provenance"] = "unverified_cached_prediction"

    gemini_indexed = gemini.set_index("sentence_id")
    gemini_valid_ids = set(gemini_valid["sentence_id"])

    for index, row in result.iterrows():
        sid = row["sentence_id"]
        if sid in gemini_valid_ids:
            result.at[index, "gemini_pred"] = gemini_indexed.at[
                sid, "prompt_pred"
            ]
            result.at[index, "gemini_valid"] = True

    # Preserve cached DistilBERT predictions for inspection only.
    model_status = "unavailable_current_checkpoint_weights_missing"
    model_alignment_status = "not_checked"

    if MODEL_PATH.exists():
        model = pd.read_csv(MODEL_PATH)
        required_model = {
            "sentence_id", "text", "label", "model_pred", "model_confidence"
        }

        if required_model.issubset(model.columns):
            validate_alignment(test, model, "DistilBERT cache", "label")
            model_alignment_status = "ids_text_and_gold_labels_aligned"

            model_indexed = model.set_index("sentence_id")
            result["distilbert_cached_pred"] = result["sentence_id"].map(
                model_indexed["model_pred"]
            )

    # Common comparison: same examples for rules and valid Gemini.
    common_ids = set(gemini_valid["sentence_id"])
    common = result[result["sentence_id"].isin(common_ids)].copy()

    if len(common) != len(gemini_valid):
        raise ValueError("Could not establish an exact common comparison set.")

    y_common = common["gold_label"].tolist()

    report = {
        "report_type": "evidence_aware_comparative_evaluation",
        "dataset": {
            "path": str(TEST_PATH.relative_to(ROOT)),
            "total_examples": len(test),
            "labels": LABELS,
            "comparison_examples": len(common),
            "comparison_sentence_ids": common["sentence_id"].tolist(),
            "same_examples_for_rules_and_gemini": True,
        },
        "provenance": {
            "rules": "fresh_predictions_from_team_rule_detector",
            "gemini": "cached_team_predictions_validity_checked",
            "distilbert": model_status,
            "gemini_invalid_rows_excluded": invalid_count,
            "distilbert_cache_alignment": model_alignment_status,
        },
        "methods": {
            "rules_all_76": {
                "status": "genuine_fresh_predictions",
                "runtime_ms": round(rules_runtime_ms, 3),
                "per_sample_ms": round(rules_runtime_ms / len(test), 4),
                **calculate_metrics(
                    test["label"].tolist(), rules_predictions
                ),
            },
            "rules_common_74": {
                "status": "genuine_fresh_predictions_same_subset_as_gemini",
                "runtime_ms": None,
                "per_sample_ms": None,
                **calculate_metrics(
                    y_common, common["rules_pred"].tolist()
                ),
            },
            "gemini_valid_common": {
                "status": "cached_valid_predictions_not_live_latency",
                "runtime_ms": None,
                "per_sample_ms": None,
                **calculate_metrics(
                    y_common, common["gemini_pred"].tolist()
                ),
            },
            "distilbert": {
                "status": model_status,
                "metrics": None,
                "runtime_ms": None,
                "per_sample_ms": None,
                "note": (
                    "Cached predictions are retained in the CSV for "
                    "traceability but are not scored as verified inference."
                ),
            },
        },
        "limitations": [
            "Gemini metrics use only valid cached responses.",
            "Gemini inference latency cannot be recovered from cached predictions.",
            "DistilBERT checkpoint weights are missing from the current workspace.",
            "Cached DistilBERT predictions are not independently verified.",
            "Rule-based multi-finding outputs are reduced using the team's "
            "primary_label priority through predict_label.",
        ],
    }

    # New filenames only. Original benchmark files remain untouched.
    result.to_csv(OUTPUT_CSV, index=False)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nEvaluation completed.")
    print("CSV:", OUTPUT_CSV)
    print("JSON:", OUTPUT_JSON)
    print("Rules examples:", len(test))
    print("Gemini valid examples:", len(gemini_valid))
    print("Gemini excluded API failures:", invalid_count)
    print("DistilBERT:", model_status)

    for method in ["rules_all_76", "rules_common_74", "gemini_valid_common"]:
        metrics = report["methods"][method]
        print(
            f"{method}: n={metrics['n_examples']}, "
            f"accuracy={metrics['accuracy']}, "
            f"macro_f1={metrics['macro_f1']}"
        )


if __name__ == "__main__":
    main()
