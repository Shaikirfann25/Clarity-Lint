"""Run the rules on a labeled CSV and summarize false positives / negatives.

    python -m src.rules.eval_dev data/splits/dev.csv

Expects columns: text, label  (sentence_id optional). Labels: no_ambiguity,
vague, attachment, scope, pronoun.

Use the DEV split only while tuning rules. Do not tune on test.csv.
Rules may flag several labels; a sentence counts as "hit" for a label if that
label appears among its predictions (multi-label view), which is fairer to the
rules than forcing one label. Use primary_label() for single-label comparison.
"""
import csv
import sys

from .common import LABELS
from .detect import detect


def main(path: str) -> None:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    records = detect([{"sentence_id": r.get("sentence_id") or f"S{i+1:03d}", "text": r["text"],
                       "gold_label": r["label"]} for i, r in enumerate(rows)])
    print(f"{len(records)} sentences from {path}\n")
    print(f"{'label':<12}{'TP':>5}{'FP':>5}{'FN':>5}{'prec':>8}{'rec':>8}{'f1':>8}")
    for label in LABELS:
        tp = fp = fn = 0
        for r in records:
            pred = any(p["label"] == label for p in r["predictions"])
            gold = r["gold_label"] == label
            tp += pred and gold
            fp += pred and not gold
            fn += gold and not pred
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        print(f"{label:<12}{tp:>5}{fp:>5}{fn:>5}{prec:>8.2f}{rec:>8.2f}{f1:>8.2f}")
    print("\nFalse positives (flagged, gold differs):")
    for r in records:
        for p in r["predictions"]:
            if r["gold_label"] != p["label"]:
                print(f"  [{r['sentence_id']}] {p['label']} '{p['span']}' (gold={r['gold_label']}): {r['text']}")
    print("\nFalse negatives (gold ambiguity type missed):")
    for r in records:
        g = r["gold_label"]
        if g in LABELS and not any(p["label"] == g for p in r["predictions"]):
            print(f"  [{r['sentence_id']}] gold={g}: {r['text']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m src.rules.eval_dev data/splits/dev.csv")
    main(sys.argv[1])
