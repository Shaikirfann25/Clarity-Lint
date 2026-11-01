# DistilBERT Ambiguity Classifier — Model Card Notes (Person 3)

## 1. Model Overview
- **Architecture**: `distilbert-base-uncased` fine-tuned for sequence classification (5 classes).
- **Owner**: Person 3 (DistilBERT Classifier & Model Comparison).
- **Task**: Multi-class single-label sentence classification to detect linguistic ambiguity in requirements, policy, and contract text.
- **Labels (5)**:
  - `no_ambiguity`
  - `vague`
  - `attachment`
  - `scope`
  - `pronoun`

## 2. Training Data & Splits
- **Dataset Provider**: Person 1 (`data/splits/`).
- **Data Splits**: 70% Train, 15% Dev (Validation), 15% Held-Out Test.
- **Leakage Prevention**: Stratified split with fixed random seed; sentence IDs frozen. Held-out test set is evaluated only once after final model selection on Dev.

## 3. Training Configuration & Hyperparameters
- **Base Model**: `distilbert-base-uncased` (~66M parameters).
- **Max Sequence Length**: 128 tokens.
- **Optimizer**: AdamW with weight decay (0.01).
- **Learning Rate**: 3e-5 (linear warmup with decay).
- **Batch Size**: 16.
- **Epochs**: 5.
- **Selection Metric**: Macro-F1 on the Dev set (checkpoint with best macro-F1 loaded at end of training).

## 4. Evaluation Strategy
- **Baseline Comparison**: Compared against Person 2's interpretable rule-based detector and Person 4's zero-shot LLM baseline on the exact same test sentences.
- **Metrics Computed**:
  - Macro-F1 (primary metric across all classes to guard against class imbalance)
  - Weighted-F1
  - Per-class Precision, Recall, and F1
  - Confusion Matrix (`outputs/model_metrics.json`)

## 5. Limitations & Responsible Use
- **Not Ground Truth for Legal Validity**: Predictions indicate statistical likelihood based on annotated patterns, not authoritative legal interpretation.
- **Calibration**: Softmax probability serves as a relative confidence score; it should not be interpreted as absolute certainty.
- **Domain Sensitivity**: Sentences substantially different from the training corpus (e.g. extremely long compound legal boilerplate) may yield reduced precision.

