"""Evaluation utilities for fair comparisons on identical examples.

All selected methods must have predictions for every evaluated row.
Missing predictions are rejected rather than silently excluded.
Metrics are calculated only from supplied gold labels and predictions.
"""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

LABELS = ["no_ambiguity", "vague", "attachment", "scope", "pronoun"]


def evaluate_predictions(df: pd.DataFrame, prediction_columns: list[str]):
    """Evaluate prediction columns on exactly the same complete rows.

    Returns:
        (evaluated_dataframe, reports_by_prediction_column)

    Raises:
        ValueError: for missing columns, empty method lists, missing values,
                    invalid labels, or an empty dataframe.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if df.empty:
        raise ValueError("Cannot evaluate an empty dataframe")

    if not prediction_columns:
        raise ValueError("At least one prediction column is required")

    if len(prediction_columns) != len(set(prediction_columns)):
        raise ValueError("Duplicate prediction columns are not allowed")

    required = ["gold_label", *prediction_columns]
    missing_columns = [column for column in required if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Required column(s) missing: {missing_columns}")

    evaluated = df.copy()

    missing_counts = evaluated[required].isna().sum()
    missing_counts = missing_counts[missing_counts > 0]
    if not missing_counts.empty:
        details = ", ".join(
            f"{column}={int(count)}" for column, count in missing_counts.items()
        )
        raise ValueError(
            "Cannot compare methods on identical examples because predictions "
            f"or gold labels are missing: {details}"
        )

    invalid_gold = set(evaluated["gold_label"].unique()) - set(LABELS)
    if invalid_gold:
        raise ValueError(f"Unexpected gold label(s): {sorted(invalid_gold)}")

    reports = {}

    for column in prediction_columns:
        invalid_predictions = set(evaluated[column].unique()) - set(LABELS)
        if invalid_predictions:
            raise ValueError(
                f"Unexpected label(s) in {column}: {sorted(invalid_predictions)}"
            )

        y_true = evaluated["gold_label"].tolist()
        y_pred = evaluated[column].tolist()

        class_report = classification_report(
            y_true,
            y_pred,
            labels=LABELS,
            output_dict=True,
            zero_division=0,
        )

        reports[column] = {
            "n_examples": len(evaluated),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_precision": float(
                precision_score(
                    y_true, y_pred, labels=LABELS,
                    average="macro", zero_division=0
                )
            ),
            "macro_recall": float(
                recall_score(
                    y_true, y_pred, labels=LABELS,
                    average="macro", zero_division=0
                )
            ),
            "macro_f1": float(
                f1_score(
                    y_true, y_pred, labels=LABELS,
                    average="macro", zero_division=0
                )
            ),
            "weighted_f1": float(
                f1_score(
                    y_true, y_pred, labels=LABELS,
                    average="weighted", zero_division=0
                )
            ),
            "per_class": {
                label: {
                    "precision": float(class_report[label]["precision"]),
                    "recall": float(class_report[label]["recall"]),
                    "f1": float(class_report[label]["f1-score"]),
                    "support": int(class_report[label]["support"]),
                }
                for label in LABELS
            },
            "confusion_matrix": confusion_matrix(
                y_true, y_pred, labels=LABELS
            ).tolist(),
        }

    return evaluated, reports


def make_demo_predictions():
    """Synthetic fixtures for UI/testing only; never real benchmark results."""
    rows = [
        ("no_ambiguity", "no_ambiguity", "no_ambiguity", "no_ambiguity"),
        ("vague", "vague", "vague", "vague"),
        ("attachment", "no_ambiguity", "attachment", "attachment"),
        ("scope", "scope", "scope", "no_ambiguity"),
        ("pronoun", "pronoun", "pronoun", "pronoun"),
        ("no_ambiguity", "vague", "no_ambiguity", "no_ambiguity"),
        ("vague", "vague", "no_ambiguity", "vague"),
        ("attachment", "attachment", "attachment", "no_ambiguity"),
        ("scope", "no_ambiguity", "scope", "scope"),
        ("pronoun", "pronoun", "no_ambiguity", "pronoun"),
    ]

    df = pd.DataFrame(
        rows,
        columns=["gold_label", "rules_pred", "model_pred", "prompt_pred"],
    )
    _, reports = evaluate_predictions(
        df, ["rules_pred", "model_pred", "prompt_pred"]
    )
    return reports
