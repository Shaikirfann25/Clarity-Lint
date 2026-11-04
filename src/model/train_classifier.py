"""Training pipeline for DistilBERT Ambiguity Classifier (Person 3).

Trains DistilBERT on data/splits/train.csv, evaluates on data/splits/dev.csv,
and generates test metrics & predictions on data/splits/test.csv.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Canonical team label space
LABEL_LIST = ["no_ambiguity", "vague", "attachment", "scope", "pronoun"]
LABEL2ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID2LABEL = {i: label for i, label in enumerate(LABEL_LIST)}


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    micro_f1 = f1_score(labels, preds, average="micro", zero_division=0)
    return {
        "macro_f1": macro_f1,
        "micro_f1": micro_f1,
    }


def load_split(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Required split file missing: {csv_path}")
    df = pd.read_csv(csv_path)
    required_cols = {"text", "label"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"{csv_path} must contain columns {required_cols}. Found: {df.columns.tolist()}")
    return df


def train(
    data_dir: Path,
    output_dir: Path,
    model_name: str = "distilbert-base-uncased",
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 3e-5,
    seed: int = 42,
    weight_decay: float = 0.01
):
    import torch
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
        DataCollatorWithPadding,
        set_seed
    )
    from datasets import Dataset

    set_seed(seed)
    logger.info(f"Using device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

    # Load splits
    train_path = data_dir / "train.csv"
    dev_path = data_dir / "dev.csv"
    test_path = data_dir / "test.csv"

    logger.info(f"Loading datasets from {data_dir}...")
    train_df = load_split(train_path)
    dev_df = load_split(dev_path)

    # Validate and map labels
    for name, df in [("train", train_df), ("dev", dev_df)]:
        invalid = set(df["label"].unique()) - set(LABEL_LIST)
        if invalid:
            raise ValueError(f"Found invalid labels in {name} split: {invalid}. Must be in {LABEL_LIST}")
        df["label_id"] = df["label"].map(LABEL2ID)

    logger.info(f"Train samples: {len(train_df)}, Dev samples: {len(dev_df)}")
    logger.info(f"Label distribution (train):\n{train_df['label'].value_counts()}")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_func(batch):
        return tokenizer(batch["text"], truncation=True, max_length=128)

    train_ds = Dataset.from_pandas(train_df[["text", "label_id"]].rename(columns={"label_id": "label"}))
    dev_ds = Dataset.from_pandas(dev_df[["text", "label_id"]].rename(columns={"label_id": "label"}))

    train_tokenized = train_ds.map(tokenize_func, batched=True)
    dev_tokenized = dev_ds.map(tokenize_func, batched=True)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Model
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL_LIST),
        id2label=ID2LABEL,
        label2id=LABEL2ID
    )

    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=epochs,
        weight_decay=weight_decay,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        seed=seed,
        logging_steps=10,
        save_total_limit=2,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=dev_tokenized,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )

    logger.info("Starting DistilBERT fine-tuning...")
    trainer.train()

    # Save final best model and tokenizer
    logger.info(f"Saving best model to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    # Evaluate on held-out test set if present
    if test_path.exists():
        logger.info(f"Evaluating best checkpoint on held-out test set: {test_path}...")
        test_df = load_split(test_path)
        test_df["label_id"] = test_df["label"].map(LABEL2ID)
        test_ds = Dataset.from_pandas(test_df[["text", "label_id"]].rename(columns={"label_id": "label"}))
        test_tokenized = test_ds.map(tokenize_func, batched=True)

        preds_raw = trainer.predict(test_tokenized)
        logits = preds_raw.predictions
        probs = torch.softmax(torch.tensor(logits), dim=-1).numpy()
        pred_ids = np.argmax(probs, axis=-1)
        confidences = np.max(probs, axis=-1)

        test_df["model_pred"] = [ID2LABEL[p] for p in pred_ids]
        test_df["model_confidence"] = np.round(confidences, 4)

        # Save predictions CSV
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        pred_csv = outputs_dir / "model_test_predictions.csv"
        test_df.to_csv(pred_csv, index=False)
        logger.info(f"Saved test predictions to {pred_csv}")

        # Metrics report
        y_true = test_df["label"]
        y_pred = test_df["model_pred"]
        report = classification_report(y_true, y_pred, labels=LABEL_LIST, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=LABEL_LIST).tolist()

        metrics_summary = {
            "model": model_name,
            "seed": seed,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "macro_f1": report["macro avg"]["f1-score"],
            "weighted_f1": report["weighted avg"]["f1-score"],
            "per_class": {
                label: {
                    "precision": report[label]["precision"],
                    "recall": report[label]["recall"],
                    "f1": report[label]["f1-score"],
                    "support": report[label]["support"]
                }
                for label in LABEL_LIST if label in report
            },
            "confusion_matrix": {
                "labels": LABEL_LIST,
                "matrix": cm
            }
        }

        metrics_json = outputs_dir / "model_metrics.json"
        with open(metrics_json, "w", encoding="utf-8") as f:
            json.dump(metrics_summary, f, indent=2)
        logger.info(f"Saved evaluation metrics to {metrics_json}")


def main():
    parser = argparse.ArgumentParser(description="Train DistilBERT Clarity Lint Classifier")
    parser.add_argument("--data_dir", type=str, default="data/splits", help="Directory with train.csv, dev.csv, test.csv")
    parser.add_argument("--output_dir", type=str, default="models/distilbert_clarity_lint", help="Where to save model")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased", help="Base pretrained transformer")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    train(
        data_dir=Path(args.data_dir),
        output_dir=Path(args.output_dir),
        model_name=args.model_name,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        seed=args.seed
    )


if __name__ == "__main__":
    main()

