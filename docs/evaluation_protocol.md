# Evaluation Protocol

1. Freeze test sentence IDs and label mapping before comparing methods.
2. Run rules, classifier and prompt baseline on the exact same test examples.
3. Report number of evaluated examples, per-class precision/recall/F1, macro-F1, and confusion matrix.
4. Keep missing predictions explicit; do not quietly drop rows for one method without documenting the difference.
5. Record machine, Python version, dependency versions, and timing method for latency.
6. Inspect 10–15 representative errors grouped by cause.
7. Report limitations, class imbalance and dataset source/annotation constraints.
8. Never use test results to tune rules, thresholds or prompts.
9. Clearly distinguish measured metrics from demo placeholders.
