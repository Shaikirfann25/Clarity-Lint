import pandas as pd
import pytest
from src.integration.evaluation import evaluate_predictions, LABELS

def test_evaluation_uses_supplied_predictions():
    df = pd.DataFrame({"gold_label":["vague","pronoun"], "rules_pred":["vague","no_ambiguity"]})
    _, reports = evaluate_predictions(df, ["rules_pred"])
    assert reports["rules_pred"]["n_examples"] == 2
    assert "macro_f1" in reports["rules_pred"]
    assert len(reports["rules_pred"]["confusion_matrix"]) == len(LABELS)

def test_invalid_label_rejected():
    df = pd.DataFrame({"gold_label":["unknown"], "rules_pred":["vague"]})
    with pytest.raises(ValueError):
        evaluate_predictions(df, ["rules_pred"])
