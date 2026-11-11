import pandas as pd
import pytest

from src.integration.evaluation import evaluate_predictions, LABELS


def test_evaluation_uses_supplied_predictions():
    df = pd.DataFrame({
        "gold_label": ["vague", "pronoun"],
        "rules_pred": ["vague", "no_ambiguity"],
    })

    evaluated, reports = evaluate_predictions(df, ["rules_pred"])
    report = reports["rules_pred"]

    assert len(evaluated) == 2
    assert report["n_examples"] == 2
    assert "accuracy" in report
    assert "macro_precision" in report
    assert "macro_recall" in report
    assert "macro_f1" in report
    assert "weighted_f1" in report
    assert set(report["per_class"]) == set(LABELS)
    assert len(report["confusion_matrix"]) == len(LABELS)


def test_invalid_label_rejected():
    df = pd.DataFrame({
        "gold_label": ["unknown"],
        "rules_pred": ["vague"],
    })

    with pytest.raises(ValueError, match="Unexpected gold label"):
        evaluate_predictions(df, ["rules_pred"])


def test_missing_prediction_rejected_instead_of_dropping_rows():
    df = pd.DataFrame({
        "gold_label": ["vague", "pronoun"],
        "rules_pred": ["vague", None],
        "model_pred": ["vague", "pronoun"],
    })

    with pytest.raises(ValueError, match="identical examples"):
        evaluate_predictions(df, ["rules_pred", "model_pred"])


def test_all_methods_use_the_same_example_count():
    df = pd.DataFrame({
        "gold_label": ["vague", "pronoun", "scope"],
        "rules_pred": ["vague", "pronoun", "scope"],
        "model_pred": ["vague", "no_ambiguity", "scope"],
        "prompt_pred": ["vague", "pronoun", "no_ambiguity"],
    })

    evaluated, reports = evaluate_predictions(
        df, ["rules_pred", "model_pred", "prompt_pred"]
    )

    assert len(evaluated) == 3
    assert {
        report["n_examples"] for report in reports.values()
    } == {3}


def test_missing_column_rejected():
    df = pd.DataFrame({"gold_label": ["vague"]})

    with pytest.raises(ValueError, match="Required column"):
        evaluate_predictions(df, ["rules_pred"])


def test_empty_prediction_column_list_rejected():
    df = pd.DataFrame({"gold_label": ["vague"]})

    with pytest.raises(ValueError, match="At least one"):
        evaluate_predictions(df, [])
