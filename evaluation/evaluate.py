"""CLI evaluation for a CSV with gold_label and prediction columns."""
import argparse
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from src.integration.evaluation import evaluate_predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="CSV with gold_label and one or more prediction columns")
    parser.add_argument("--output", default="outputs/cli_evaluation_report.json")
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    preds = [c for c in ["rules_pred", "model_pred", "prompt_pred"] if c in df.columns]
    if not preds:
        raise SystemExit("Need at least one of rules_pred, model_pred, prompt_pred.")
    _, reports = evaluate_predictions(df, preds)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(f"Wrote calculated reports to {out}")
    print("Ensure this CSV uses the frozen held-out test set.")


if __name__ == "__main__":
    main()
