"""Preprocessing module for Clarity Lint.

Handles dataset loading, schema validation, quality checks, meaning-preserving
cleaning, near-duplicate template detection, and template-aware stratified
train/dev/test splits.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Canonical five labels defined in annotation guide and integration contract
LABELS: List[str] = ["no_ambiguity", "vague", "attachment", "scope", "pronoun"]

DEFAULT_REQUIRED_COLUMNS: List[str] = ["sentence_id", "text", "label"]


def load_dataset(filepath: str | Path) -> pd.DataFrame:
    """Load a CSV dataset and perform initial checks.

    Args:
        filepath: Path to the dataset CSV.

    Returns:
        pd.DataFrame containing the loaded dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or cannot be parsed as a DataFrame.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file not found at: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV at {path}: {e}") from e

    if df.empty:
        raise ValueError(f"Dataset file at {path} is empty.")

    # Accommodate 'sentence' as an alias for 'text' if needed
    if "text" not in df.columns and "sentence" in df.columns:
        df = df.rename(columns={"sentence": "text"})

    return df


def validate_schema(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    allowed_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Validate dataset schema, missing values, allowed labels, and duplicates.

    Args:
        df: DataFrame to validate.
        required_columns: List of columns that must be present.
        allowed_labels: List of valid ambiguity categories.

    Returns:
        Dictionary summarizing validation results and quality metrics.

    Raises:
        ValueError: If required columns are missing or if invalid labels exist.
    """
    req_cols = required_columns or DEFAULT_REQUIRED_COLUMNS
    valid_labels = set(allowed_labels or LABELS)

    # 1. Column presence check
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    # 2. Missing value checks
    null_counts = {col: int(df[col].isnull().sum()) for col in df.columns}
    empty_string_counts = {}
    for col in df.columns:
        if df[col].dtype == object:
            empty_string_counts[col] = int((df[col].astype(str).str.strip() == "").sum())

    total_missing = sum(null_counts[c] for c in req_cols) + sum(
        empty_string_counts.get(c, 0) for c in req_cols
    )

    # 3. Label validation
    actual_labels = set(df["label"].dropna().unique())
    invalid_labels = sorted(list(actual_labels - valid_labels))
    if invalid_labels:
        raise ValueError(f"Found invalid labels in dataset: {invalid_labels}. Allowed: {sorted(list(valid_labels))}")

    # 4. Duplicate checks
    text_col = "text"
    exact_duplicates = int(df[text_col].duplicated().sum())
    norm_texts = df[text_col].astype(str).str.strip().str.lower()
    case_insensitive_duplicates = int(norm_texts.duplicated().sum())

    # 5. Sentence ID uniqueness
    id_unique = bool(df["sentence_id"].is_unique) if "sentence_id" in df.columns else None

    # 6. Label distribution
    label_dist = {label: int(count) for label, count in df["label"].value_counts().items()}

    return {
        "is_valid": total_missing == 0 and len(invalid_labels) == 0,
        "row_count": len(df),
        "columns": list(df.columns),
        "missing_columns": missing_cols,
        "null_counts": null_counts,
        "empty_string_counts": empty_string_counts,
        "invalid_labels": invalid_labels,
        "exact_duplicates": exact_duplicates,
        "case_insensitive_duplicates": case_insensitive_duplicates,
        "sentence_id_unique": id_unique,
        "label_distribution": label_dist,
    }


def clean_text(text: str) -> str:
    """Perform meaning-preserving text cleaning.

    Preserves capitalization, acronyms, and grammatical punctuation necessary for
    syntactic attachment, scope, and pronoun disambiguation. Does NOT apply stemming,
    lemmatization, or destructive normalization.

    Args:
        text: Raw input sentence string.

    Returns:
        Cleaned sentence string.
    """
    if not isinstance(text, str):
        return ""

    # Replace non-breaking spaces and zero-width spaces with standard space
    cleaned = text.replace("\u00a0", " ").replace("\u200b", "")

    # Normalize typographic quotes to straight quotes for consistency
    cleaned = cleaned.replace("“", '"').replace("”", '"')
    cleaned = cleaned.replace("‘", "'").replace("’", "'")

    # Normalize em-dash and en-dash to hyphen or surrounded spaced hyphen
    cleaned = cleaned.replace("—", " — ").replace("–", " - ")

    # Collapse multiple consecutive whitespace characters into a single space
    cleaned = re.sub(r"[ \t\r\f\v]+", " ", cleaned)

    # Trim leading and trailing whitespace
    cleaned = cleaned.strip()

    return cleaned


def clean_dataset(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    """Apply meaning-preserving text cleaning across a DataFrame.

    Args:
        df: Input DataFrame.
        text_column: Column name containing the sentence strings.

    Returns:
        A copy of the DataFrame with cleaned text and stripped string columns.
    """
    cleaned_df = df.copy()

    # Clean text column
    cleaned_df[text_column] = cleaned_df[text_column].apply(clean_text)

    # Trim any whitespace on string columns such as label or sentence_id
    for col in ["sentence_id", "label", "source_type"]:
        if col in cleaned_df.columns and cleaned_df[col].dtype == object:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

    # Verify no sentence became empty
    empty_rows = (cleaned_df[text_column] == "").sum()
    if empty_rows > 0:
        raise ValueError(f"Cleaning resulted in {empty_rows} empty sentences.")

    return cleaned_df


def _get_word_tokens(text: str) -> Set[str]:
    """Helper to extract lowercased word tokens for lexical similarity."""
    return set(re.findall(r"\b\w+\b", text.lower()))


def detect_template_similarity(
    df: pd.DataFrame,
    text_column: str = "text",
    threshold: float = 0.50,
) -> List[Dict[str, Any]]:
    """Detect pairs of sentences exhibiting high lexical/template overlap.

    Computes pairwise Jaccard similarity over word token sets to find near-duplicates
    or heavily shared syntactic templates.

    Args:
        df: DataFrame containing sentences.
        text_column: Column name containing the sentence strings.
        threshold: Minimum Jaccard similarity to flag as a template pair (default 0.50).

    Returns:
        List of flagged pairs with IDs, labels, texts, and similarity scores.
    """
    pairs: List[Dict[str, Any]] = []
    records = df[[col for col in ["sentence_id", text_column, "label"] if col in df.columns]].to_dict("records")
    n = len(records)

    token_sets = [_get_word_tokens(r[text_column]) for r in records]

    for i in range(n):
        words_i = token_sets[i]
        if not words_i:
            continue
        for j in range(i + 1, n):
            words_j = token_sets[j]
            if not words_j:
                continue

            intersection = len(words_i & words_j)
            union = len(words_i | words_j)
            jaccard = intersection / union if union > 0 else 0.0

            if jaccard >= threshold:
                pairs.append({
                    "id_1": records[i].get("sentence_id", str(i)),
                    "id_2": records[j].get("sentence_id", str(j)),
                    "label_1": records[i].get("label", "unknown"),
                    "label_2": records[j].get("label", "unknown"),
                    "jaccard_similarity": round(jaccard, 3),
                    "text_1": records[i][text_column],
                    "text_2": records[j][text_column],
                })

    return sorted(pairs, key=lambda x: x["jaccard_similarity"], reverse=True)


def create_stratified_splits(
    df: pd.DataFrame,
    train_size: float = 0.70,
    dev_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
    label_column: str = "label",
    group_templates: bool = True,
    similarity_threshold: float = 0.50,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create reproducible, stratified train/dev/test splits.

    When group_templates=True, detects connected components of sentences with
    word-level Jaccard similarity >= similarity_threshold and keeps all template
    variants together in the training partition, eliminating template leakage into
    held-out evaluation sets while strictly preserving per-class stratification.

    Args:
        df: Input DataFrame.
        train_size: Proportion for training (e.g. 0.70).
        dev_size: Proportion for validation (e.g. 0.15).
        test_size: Proportion for testing (e.g. 0.15).
        random_state: Random seed for reproducibility (fixed at 42).
        label_column: Target label column used for stratification.
        group_templates: Whether to group similar templates into the same split.
        similarity_threshold: Jaccard similarity threshold for template grouping.

    Returns:
        Tuple of (train_df, dev_df, test_df).

    Raises:
        ValueError: If split proportions do not sum to 1.0.
    """
    total_prop = train_size + dev_size + test_size
    if not (0.999 <= total_prop <= 1.001):
        raise ValueError(f"Split proportions must sum to 1.0; got {total_prop:.4f}")

    if not group_templates:
        # Fall back to standard stratified splitting
        temp_size = dev_size + test_size
        train_df, temp_df = train_test_split(
            df,
            test_size=temp_size,
            random_state=random_state,
            stratify=df[label_column],
        )
        dev_proportion_of_temp = dev_size / temp_size
        dev_df, test_df = train_test_split(
            temp_df,
            train_size=dev_proportion_of_temp,
            random_state=random_state,
            stratify=temp_df[label_column],
        )
    else:
        # Template-group-aware stratified splitting
        token_sets = [_get_word_tokens(t) for t in df["text"]]
        n = len(df)

        # 1. Build adjacency graph of template similarities
        adj: List[List[int]] = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                inter = len(token_sets[i] & token_sets[j])
                union = len(token_sets[i] | token_sets[j])
                if union > 0 and (inter / union) >= similarity_threshold:
                    adj[i].append(j)
                    adj[j].append(i)

        # 2. Extract connected components
        visited: Set[int] = set()
        multi_components: List[List[int]] = []
        singleton_indices: List[int] = []
        for i in range(n):
            if i not in visited:
                comp: List[int] = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop()
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                if len(comp) > 1:
                    multi_components.append(comp)
                else:
                    singleton_indices.append(comp[0])

        # Assign all multi-item template components to train
        train_indices: List[int] = []
        for c in multi_components:
            train_indices.extend(c)

        singletons_df = df.iloc[singleton_indices].copy()
        total_label_counts = df[label_column].value_counts()

        # Compute exact quota targets per label
        train_needed: Dict[str, int] = {}
        dev_needed: Dict[str, int] = {}
        test_needed: Dict[str, int] = {}

        assigned_train = df.iloc[train_indices][label_column].value_counts().to_dict()

        for lbl, count in total_label_counts.items():
            # Standard rounding: 70% train, 15% dev, 15% test
            t_target = round(count * train_size)
            d_target = round(count * dev_size)
            s_target = count - t_target - d_target

            already_t = assigned_train.get(lbl, 0)
            train_needed[lbl] = t_target - already_t
            dev_needed[lbl] = d_target
            test_needed[lbl] = s_target

        dev_indices: List[int] = []
        test_indices: List[int] = []

        # Partition singletons deterministically per label using random_state
        for lbl in total_label_counts.keys():
            lbl_singletons = singletons_df[singletons_df[label_column] == lbl].index.tolist()
            lbl_shuffled = pd.Series(lbl_singletons).sample(frac=1.0, random_state=random_state).tolist()

            n_t = train_needed[lbl]
            n_d = dev_needed[lbl]
            n_s = test_needed[lbl]

            train_indices.extend(lbl_shuffled[:n_t])
            dev_indices.extend(lbl_shuffled[n_t : n_t + n_d])
            test_indices.extend(lbl_shuffled[n_t + n_d : n_t + n_d + n_s])

        train_df = df.iloc[train_indices].copy()
        dev_df = df.iloc[dev_indices].copy()
        test_df = df.iloc[test_indices].copy()

    # Verify no ID leakage across splits
    if "sentence_id" in df.columns:
        train_ids = set(train_df["sentence_id"])
        dev_ids = set(dev_df["sentence_id"])
        test_ids = set(test_df["sentence_id"])

        overlap_td = train_ids & dev_ids
        overlap_tt = train_ids & test_ids
        overlap_dt = dev_ids & test_ids

        if overlap_td or overlap_tt or overlap_dt:
            raise RuntimeError(
                f"Split leakage detected! Overlaps: train-dev={len(overlap_td)}, "
                f"train-test={len(overlap_tt)}, dev-test={len(overlap_dt)}"
            )

    return train_df.reset_index(drop=True), dev_df.reset_index(drop=True), test_df.reset_index(drop=True)


def check_cross_split_leakage(
    train_df: pd.DataFrame,
    dev_df: pd.DataFrame,
    test_df: pd.DataFrame,
    text_column: str = "text",
    threshold: float = 0.50,
) -> List[Dict[str, Any]]:
    """Verify that similar sentence templates do not leak across splits.

    Args:
        train_df: Training set.
        dev_df: Development/Validation set.
        test_df: Test set.
        text_column: Column name containing sentence text.
        threshold: Jaccard similarity threshold for flagging potential leakage.

    Returns:
        List of cross-split pairs exceeding the similarity threshold.
    """
    leakage_pairs: List[Dict[str, Any]] = []

    splits = [("train", train_df), ("dev", dev_df), ("test", test_df)]

    # Check pairwise cross-split comparisons (train vs dev, train vs test, dev vs test)
    for idx_a in range(len(splits)):
        name_a, df_a = splits[idx_a]
        recs_a = df_a.to_dict("records")
        tokens_a = [_get_word_tokens(r[text_column]) for r in recs_a]

        for idx_b in range(idx_a + 1, len(splits)):
            name_b, df_b = splits[idx_b]
            recs_b = df_b.to_dict("records")
            tokens_b = [_get_word_tokens(r[text_column]) for r in recs_b]

            for i in range(len(recs_a)):
                words_i = tokens_a[i]
                if not words_i:
                    continue
                for j in range(len(recs_b)):
                    words_j = tokens_b[j]
                    if not words_j:
                        continue

                    inter = len(words_i & words_j)
                    union = len(words_i | words_j)
                    sim = inter / union if union > 0 else 0.0

                    if sim >= threshold:
                        leakage_pairs.append({
                            "split_1": name_a,
                            "id_1": recs_a[i].get("sentence_id", str(i)),
                            "label_1": recs_a[i].get("label", "unknown"),
                            "text_1": recs_a[i][text_column],
                            "split_2": name_b,
                            "id_2": recs_b[j].get("sentence_id", str(j)),
                            "label_2": recs_b[j].get("label", "unknown"),
                            "text_2": recs_b[j][text_column],
                            "similarity": round(sim, 3),
                        })

    return leakage_pairs


def save_splits(
    train_df: pd.DataFrame,
    dev_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str | Path,
) -> Dict[str, Path]:
    """Save the train, dev, and test sets to CSV files.

    Args:
        train_df: Training set.
        dev_df: Development set.
        test_df: Test set.
        output_dir: Directory where split CSVs will be saved.

    Returns:
        Dictionary mapping split name ('train', 'dev', 'test') to saved file Path.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "train": out_dir / "train.csv",
        "dev": out_dir / "dev.csv",
        "test": out_dir / "test.csv",
    }

    train_df.to_csv(paths["train"], index=False)
    dev_df.to_csv(paths["dev"], index=False)
    test_df.to_csv(paths["test"], index=False)

    logger.info(f"Saved {len(train_df)} train rows to {paths['train']}")
    logger.info(f"Saved {len(dev_df)} dev rows to {paths['dev']}")
    logger.info(f"Saved {len(test_df)} test rows to {paths['test']}")

    return paths


def run_pipeline(
    input_path: str | Path = "data/clarity_lint_full_dataset.csv",
    output_dir: str | Path = "data/splits",
    random_state: int = 42,
    group_templates: bool = True,
) -> Dict[str, Any]:
    """Execute end-to-end preprocessing pipeline.

    Loads dataset, validates schema, applies meaning-preserving cleaning,
    evaluates template similarity, creates stratified splits, checks cross-split
    leakage, and saves partition files.

    Args:
        input_path: Path to original full dataset.
        output_dir: Destination directory for train/dev/test splits.
        random_state: Fixed random seed for split reproducibility.
        group_templates: Whether to keep similar sentence templates together in training.

    Returns:
        Dictionary report of the execution.
    """
    # 1. Load
    raw_df = load_dataset(input_path)

    # 2. Validate raw schema
    val_report = validate_schema(raw_df)

    # 3. Clean
    cleaned_df = clean_dataset(raw_df)

    # 4. Check internal template similarity
    template_pairs = detect_template_similarity(cleaned_df, threshold=0.50)

    # 5. Create template-aware stratified splits
    train_df, dev_df, test_df = create_stratified_splits(
        cleaned_df,
        train_size=0.70,
        dev_size=0.15,
        test_size=0.15,
        random_state=random_state,
        group_templates=group_templates,
    )

    # 6. Check cross-split template leakage
    cross_split_leakage = check_cross_split_leakage(train_df, dev_df, test_df, threshold=0.50)

    # 7. Save splits
    saved_paths = save_splits(train_df, dev_df, test_df, output_dir)

    return {
        "input_path": str(input_path),
        "total_rows": len(cleaned_df),
        "validation": val_report,
        "template_pairs_count": len(template_pairs),
        "template_pairs": template_pairs,
        "splits": {
            "train_count": len(train_df),
            "dev_count": len(dev_df),
            "test_count": len(test_df),
            "train_labels": train_df["label"].value_counts().to_dict(),
            "dev_labels": dev_df["label"].value_counts().to_dict(),
            "test_labels": test_df["label"].value_counts().to_dict(),
            "paths": {k: str(v) for k, v in saved_paths.items()},
        },
        "cross_split_leakage": cross_split_leakage,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Clarity Lint Preprocessing and Stratified Splitting")
    parser.add_argument("--input", default="data/clarity_lint_full_dataset.csv", help="Input dataset CSV")
    parser.add_argument("--output-dir", default="data/splits", help="Output directory for split CSVs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stratified splits")
    parser.add_argument("--no-group-templates", dest="group_templates", action="store_false", help="Disable template grouping")
    parser.set_defaults(group_templates=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    report = run_pipeline(
        input_path=args.input,
        output_dir=args.output_dir,
        random_state=args.seed,
        group_templates=args.group_templates,
    )

    print("\n" + "=" * 60)
    print("CLARITY LINT PREPROCESSING PIPELINE COMPLETED")
    print("=" * 60)
    print(f"Total Rows Processed: {report['total_rows']}")
    print(f"Train Split: {report['splits']['train_count']} rows")
    print(f"Dev Split:   {report['splits']['dev_count']} rows")
    print(f"Test Split:  {report['splits']['test_count']} rows")
    print("\nLabel Distribution per Split:")
    print("  Train:", report['splits']['train_labels'])
    print("  Dev:  ", report['splits']['dev_labels'])
    print("  Test: ", report['splits']['test_labels'])
    print(f"\nInternal Template Pairs (>=0.50 Jaccard): {report['template_pairs_count']}")
    print(f"Cross-Split Leakage Pairs (>=0.50 Jaccard): {len(report['cross_split_leakage'])}")
    for leak in report['cross_split_leakage']:
        print(f"  - [{leak['split_1']} {leak['id_1']}] <-> [{leak['split_2']} {leak['id_2']}] (sim={leak['similarity']})")
    print("=" * 60)


if __name__ == "__main__":
    main()
