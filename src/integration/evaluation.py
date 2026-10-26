"""Evaluation utilities for identical gold/prediction rows.

Expected CSV columns: gold_label plus any of rules_pred, model_pred, prompt_pred.
All reported scores are calculated from supplied data; this module never invents real results.
"""
from __future__ import annotations
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score

LABELS = ["no_ambiguity", "vague", "attachment", "scope", "pronoun"]

def evaluate_predictions(df: pd.DataFrame, prediction_columns: list[str]):
    if "gold_label" not in df.columns:
        raise ValueError("Required column missing: gold_label")
    reports = {}
    for col in prediction_columns:
        subset = df[["gold_label", col]].dropna()
        invalid = (set(subset["gold_label"]) | set(subset[col])) - set(LABELS)
        if invalid:
            raise ValueError(f"Unexpected label(s) in {col}: {sorted(invalid)}")
        y_true, y_pred = subset["gold_label"].tolist(), subset[col].tolist()
        reports[col] = {
            "n_examples": len(subset),
            "accuracy": float(accuracy_score(y_true, y_pred)) if len(subset) else 0.0,
            "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)) if len(subset) else 0.0,
            "per_class": classification_report(y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist()
        }
    return df, reports

def make_demo_predictions():
    # Synthetic fixture ONLY to verify visualizations and evaluation code paths.
    rows = [
      ("no_ambiguity","no_ambiguity","no_ambiguity","no_ambiguity"),
      ("vague","vague","vague","vague"),
      ("attachment","no_ambiguity","attachment","attachment"),
      ("scope","scope","scope","no_ambiguity"),
      ("pronoun","pronoun","pronoun","pronoun"),
      ("no_ambiguity","vague","no_ambiguity","no_ambiguity"),
      ("vague","vague","no_ambiguity","vague"),
      ("attachment","attachment","attachment","no_ambiguity"),
      ("scope","no_ambiguity","scope","scope"),
      ("pronoun","pronoun","no_ambiguity","pronoun"),
    ]
    df = pd.DataFrame(rows, columns=["gold_label","rules_pred","model_pred","prompt_pred"])
    _, reports = evaluate_predictions(df, ["rules_pred","model_pred","prompt_pred"])
    return reports
