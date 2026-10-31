from pathlib import Path
import pandas as pd
import pytest

from src.preprocessing.preprocess import (
    LABELS,
    clean_dataset,
    clean_text,
    create_stratified_splits,
    detect_template_similarity,
    check_cross_split_leakage,
    load_dataset,
    save_splits,
    validate_schema,
)


@pytest.fixture
def sample_df():
    data = [
        {"sentence_id": "S001", "text": "The system should respond quickly.", "label": "vague"},
        {"sentence_id": "S002", "text": "She saw the man with the telescope.", "label": "attachment"},
        {"sentence_id": "S003", "text": "Every student did not pass.", "label": "scope"},
        {"sentence_id": "S004", "text": "When Maya called Riya she was glad.", "label": "pronoun"},
        {"sentence_id": "S005", "text": "The server responds in 200ms.", "label": "no_ambiguity"},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def full_df():
    path = Path("data/clarity_lint_full_dataset.csv")
    if not path.exists():
        pytest.skip("Full dataset CSV not found")
    return load_dataset(path)


def test_load_dataset_success(full_df):
    assert len(full_df) == 507
    assert "sentence_id" in full_df.columns
    assert "text" in full_df.columns
    assert "label" in full_df.columns


def test_load_dataset_nonexistent():
    with pytest.raises(FileNotFoundError):
        load_dataset("data/nonexistent_file.csv")


def test_validate_schema_success(sample_df):
    report = validate_schema(sample_df)
    assert report["is_valid"] is True
    assert report["row_count"] == 5
    assert report["exact_duplicates"] == 0
    assert len(report["invalid_labels"]) == 0


def test_validate_schema_invalid_label(sample_df):
    sample_df.loc[0, "label"] = "invalid_category"
    with pytest.raises(ValueError, match="Found invalid labels"):
        validate_schema(sample_df)


def test_validate_schema_missing_column(sample_df):
    dropped = sample_df.drop(columns=["label"])
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_schema(dropped)


def test_clean_text_preserves_meaning_and_punctuation():
    raw = '  “The   system   should   respond   soon.”  '
    cleaned = clean_text(raw)
    assert cleaned == '"The system should respond soon."'
    assert "soon" in cleaned
    assert cleaned.endswith('."')

    # Non-breaking space test
    nbsp_text = "The\u00a0team\u00a0arrived."
    assert clean_text(nbsp_text) == "The team arrived."

    # Dash normalization test
    dash_text = "System A—the core—failed."
    assert clean_text(dash_text) == "System A — the core — failed."


def test_clean_dataset(sample_df):
    sample_df.loc[0, "text"] = "  The system  should respond quickly.  "
    cleaned = clean_dataset(sample_df)
    assert cleaned.loc[0, "text"] == "The system should respond quickly."


def test_clean_dataset_empty_error(sample_df):
    sample_df.loc[0, "text"] = "   "
    with pytest.raises(ValueError, match="empty sentences"):
        clean_dataset(sample_df)


def test_create_stratified_splits_with_grouping(full_df):
    train_df, dev_df, test_df = create_stratified_splits(
        full_df, train_size=0.70, dev_size=0.15, test_size=0.15, random_state=42, group_templates=True
    )

    # Count checks (355 train, 76 dev, 76 test)
    assert len(train_df) == 355
    assert len(dev_df) == 76
    assert len(test_df) == 76
    assert len(train_df) + len(dev_df) + len(test_df) == 507

    # Disjoint ID check
    train_ids = set(train_df["sentence_id"])
    dev_ids = set(dev_df["sentence_id"])
    test_ids = set(test_df["sentence_id"])

    assert len(train_ids & dev_ids) == 0
    assert len(train_ids & test_ids) == 0
    assert len(dev_ids & test_ids) == 0

    # Stratification check: all labels represented in each split
    for label in LABELS:
        assert (train_df["label"] == label).sum() >= 70
        assert (dev_df["label"] == label).sum() == (16 if label == "pronoun" else 15)
        assert (test_df["label"] == label).sum() == (16 if label == "pronoun" else 15)

    # Cross-split leakage check: should be exactly 0
    leaks = check_cross_split_leakage(train_df, dev_df, test_df, threshold=0.50)
    assert len(leaks) == 0


def test_create_stratified_splits_standard(full_df):
    train_df, dev_df, test_df = create_stratified_splits(
        full_df, train_size=0.70, dev_size=0.15, test_size=0.15, random_state=42, group_templates=False
    )
    assert len(train_df) + len(dev_df) + len(test_df) == 507
    assert len(set(train_df["sentence_id"]) & set(test_df["sentence_id"])) == 0


def test_detect_template_similarity():
    df = pd.DataFrame([
        {"sentence_id": "T1", "text": "Every engineer validated the hardware interface.", "label": "scope"},
        {"sentence_id": "T2", "text": "Every engineer validated the software interface.", "label": "scope"},
        {"sentence_id": "T3", "text": "Completely unrelated sentence with distinct terms.", "label": "no_ambiguity"},
    ])
    pairs = detect_template_similarity(df, threshold=0.50)
    assert len(pairs) == 1
    assert pairs[0]["id_1"] == "T1"
    assert pairs[0]["id_2"] == "T2"
    assert pairs[0]["jaccard_similarity"] > 0.50


def test_check_cross_split_leakage():
    train_df = pd.DataFrame([{"sentence_id": "TR1", "text": "The manager validated the report.", "label": "vague"}])
    dev_df = pd.DataFrame([{"sentence_id": "DV1", "text": "The manager validated the report.", "label": "vague"}])
    test_df = pd.DataFrame([{"sentence_id": "TS1", "text": "Completely different text here.", "label": "vague"}])

    leaks = check_cross_split_leakage(train_df, dev_df, test_df, threshold=0.80)
    assert len(leaks) == 1
    assert leaks[0]["id_1"] == "TR1"
    assert leaks[0]["id_2"] == "DV1"
    assert leaks[0]["similarity"] == 1.0


def test_save_splits(sample_df, tmp_path):
    train_df = sample_df.iloc[:3]
    dev_df = sample_df.iloc[3:4]
    test_df = sample_df.iloc[4:5]

    paths = save_splits(train_df, dev_df, test_df, tmp_path)

    assert paths["train"].exists()
    assert paths["dev"].exists()
    assert paths["test"].exists()

    loaded_train = pd.read_csv(paths["train"])
    assert len(loaded_train) == 3
