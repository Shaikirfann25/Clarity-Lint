# Clarity Lint — Preprocessing & Stratified Splitting Report

**Author / Role:** Shaik Irfan (Person 1 — Dataset, Annotation & Preprocessing)  
**Date:** October 31, 2026  
**Dataset Version:** Full Synthetic Corpus (`data/clarity_lint_full_dataset.csv`, 507 sentences)  
**Seed for Reproducibility:** `random_state=42`  
**Splitting Strategy:** Template-Aware Stratified Partitioning (`group_templates=True`)

---

## 1. Executive Summary

As part of the **Person 1** deliverable, the preprocessing module has been implemented, quality-reviewed, and verified. The module provides:
- Automated CSV loading and strict schema validation.
- Missing-value, empty-string, and duplicate detection.
- Meaning-preserving text cleaning tailored specifically for grammatical ambiguity detection.
- Pairwise template similarity detection and cross-split leakage auditing.
- Template-aware stratified partitioning into **Train (70.0%)**, **Validation/Dev (15.0%)**, and **Test (15.0%)** splits.
- A comprehensive unit test suite in `tests/test_preprocessing.py` (all 19 project tests passing).

The original dataset file (`data/clarity_lint_full_dataset.csv`) is strictly preserved untouched. Downstream modules (DistilBERT fine-tuning by Aman, Rule-based detection by Sudharshan, Zero-shot baseline by Rajiv, and Integration by Chaitu) can now consume fixed, reproducible data splits with zero cross-split template leakage.

---

## 2. Dataset Overview & Validation Findings

The full corpus contains **507 sentences** authored synthetically to represent requirements, policy, and contract statements.

### 2.1 Schema & Integrity Audit

| Metric | Measured Value | Validation Status |
|---|---|---|
| **Total Rows** | 507 | Verified |
| **Columns Present** | `sentence_id`, `text`, `label`, `explanation`, `source_type` | Valid (All required columns present) |
| **Null / Missing Values** | 0 | Clean |
| **Empty Strings (`""`)** | 0 | Clean |
| **Exact Duplicate Texts** | 0 | Clean |
| **Case-Insensitive Duplicates** | 0 | Clean |
| **Unique Sentence IDs** | 507 (`S001` through `S507`) | 100% Unique |
| **Punctuation Integrity** | 507 / 507 sentences end in `.`, `?`, or `!` | Clean |
| **Explanation Completeness** | 507 / 507 sentences have human justification | Clean |

### 2.2 Canonical Label Verification

All labels strictly conform to the 5 agreed categories:
- `pronoun`: 107 (21.10%)
- `vague`: 100 (19.72%)
- `attachment`: 100 (19.72%)
- `scope`: 100 (19.72%)
- `no_ambiguity`: 100 (19.72%)

*Note on Class Distribution:* `pronoun` has 107 instances while the other four categories have 100. This minor variance is preserved without synthetic dropping to avoid silently discarding annotated data.

---

## 3. Meaning-Preserving Cleaning Process

Natural Language Processing for ambiguity detection requires specific cleaning rules compared to standard topic classification:

1. **No Stemming or Lemmatization:**
   - Ambiguity often hinges on exact morphology (e.g., singular vs. plural pronouns `"they"` vs `"he"`, verb tenses, and participle forms like `"-ing"` in attachment ambiguity). Stemming or lemmatization destroys grammatical cues.
2. **Preservation of Casing:**
   - Capitalization is retained to preserve acronyms (`HTTP`, `JSON`, `API`, `UTC`) and named entities (`Priya`, `Ananya`, `Maya`) critical for pronoun coreference resolution.
3. **Preservation of Punctuation:**
   - Punctuation marks (commas, periods, quotation marks, hyphens) are fundamental to attachment boundaries and negation scopes (e.g., *"She does not like coffee, or tea"* vs *"She does not like coffee or tea"*).
4. **Standardization Performed:**
   - Leading and trailing whitespace stripped.
   - Non-breaking spaces (`\u00a0`) and zero-width spaces (`\u200b`) converted to standard ASCII spaces.
   - Consecutive redundant whitespace collapsed to a single space.
   - Typographic curly quotes (`“”‘’`) normalized to standard quotes (`""''`).
   - Em-dashes (`—`) and en-dashes (`–`) normalized with clean spacing.
5. **No Manual Pre-Tokenization:**
   - The cleaned output remains raw natural language strings so that Hugging Face's `AutoTokenizer.from_pretrained('distilbert-base-uncased')` can apply subword tokenization without whitespace artifact corruption.

---

## 4. Template Similarity & Cross-Split Optimization

### 4.1 Internal Template Pairs Identified ($\text{Jaccard} \ge 0.50$)
A token-level pairwise Jaccard analysis across all 128,271 sentence combinations revealed only **3 pairs** exceeding 0.50 similarity:
1. **`S225` $\leftrightarrow$ `S275` (Similarity = 0.700, Label: `scope`):**
   - *Sentence 1:* "Every engineer validated the hardware or the software interface."
   - *Sentence 2:* "Every engineer validated the hardware interface and the software configuration."
2. **`S360` $\leftrightarrow$ `S361` (Similarity = 0.500, Label: `pronoun`):**
   - *Sentence 1:* "The administrator found the misconfiguration in the firewall rule and updated it immediately."
   - *Sentence 2:* "The administrator found the vulnerability in the plugin and removed it immediately."
3. **`S022` $\leftrightarrow$ `S093` (Similarity = 0.571, Label: `vague`):**
   - *Sentence 1 (S022):* "The migration script should complete in a reasonable amount of time."
   - *Sentence 2 (S093):* "The repair should be completed in a reasonable amount of time."

### 4.2 Investigation of S093 vs. S022 & Template-Group Stratification
Under naive random stratified splitting, `S093` fell into Dev while `S022` fell into Test. While this was not a train-set leakage, having near-identical templates in both Dev and Test could cause validation metrics to over-estimate test performance.

To solve this, `create_stratified_splits` was enhanced with **Template-Aware Grouping (`group_templates=True`)**:
- Connected components of sentences with token Jaccard $\ge 0.50$ are identified.
- All multi-sentence template components are placed together in the **Train split**.
- The remaining 501 singletons are stratified deterministically (`random_state=42`) across Train, Dev, and Test to hit exact quota targets.
- **Outcome:** Cross-split template leakage across ALL partitions is reduced to **exactly 0**.

---

## 5. Stratified Dataset Splits

The dataset was partitioned using template-aware stratified splitting (`random_state=42`).

### 5.1 Split Proportions & Counts

| Split | Target Proportion | Actual Sentence Count | Percentage of Total |
|---|---|---|---|
| **Train (`data/splits/train.csv`)** | 70% | **355** | 70.02% |
| **Dev / Validation (`data/splits/dev.csv`)** | 15% | **76** | 14.99% |
| **Test (`data/splits/test.csv`)** | 15% | **76** | 14.99% |
| **Total** | 100% | **507** | 100.00% |

### 5.2 Per-Class Label Stratification

| Label | Full Dataset | Train Split (70%) | Dev Split (15%) | Test Split (15%) |
|---|---|---|---|---|
| **`attachment`** | 100 | 70 (19.72%) | 15 (19.74%) | 15 (19.74%) |
| **`no_ambiguity`** | 100 | 70 (19.72%) | 15 (19.74%) | 15 (19.74%) |
| **`pronoun`** | 107 | 75 (21.13%) | 16 (21.05%) | 16 (21.05%) |
| **`scope`** | 100 | 70 (19.72%) | 15 (19.74%) | 15 (19.74%) |
| **`vague`** | 100 | 70 (19.72%) | 15 (19.74%) | 15 (19.74%) |
| **Total** | **507** | **355** | **76** | **76** |

### 5.3 ID Leakage & Mutual Exclusivity Verification
- Intersection $(\text{Train} \cap \text{Dev}) = \emptyset$ (0 IDs).
- Intersection $(\text{Train} \cap \text{Test}) = \emptyset$ (0 IDs).
- Intersection $(\text{Dev} \cap \text{Test}) = \emptyset$ (0 IDs).
- $\text{Train} \cup \text{Dev} \cup \text{Test} = \text{Full Dataset}$ (all 507 IDs accounted for exactly once).
- **Cross-split pairs with Jaccard $\ge 0.50$:** **0 pairs**.

---

## 6. Implementation Manifest

| File Path | Description |
|---|---|
| `src/preprocessing/preprocess.py` | Core preprocessing pipeline with functions for loading, validation, cleaning, similarity detection, template grouping, and splitting. |
| `src/preprocessing/__init__.py` | Package exports for modular access by teammates. |
| `data/splits/train.csv` | Frozen training partition (355 rows). |
| `data/splits/dev.csv` | Frozen validation partition (76 rows). |
| `data/splits/test.csv` | Frozen held-out test partition (76 rows). |
| `tests/test_preprocessing.py` | Automated unit tests verifying loading, validation, cleaning, splitting, leakage prevention, and serialization. |
| `conftest.py` | Pytest path resolution configuration ensuring root discovery. |
| `docs/preprocessing_report.md` | This technical report. |

---

## 7. Instructions for Downstream Teammates

1. **Aman (DistilBERT Classifier):**
   - Train the classifier strictly on `data/splits/train.csv`.
   - Perform hyperparameter tuning and early stopping on `data/splits/dev.csv`.
   - **Do NOT touch `data/splits/test.csv`** until the final evaluation run.
2. **Sudharshan (Rule-Based Detection):**
   - Tune linguistic regexes and spaCy patterns using `train.csv` and `dev.csv` only.
   - Run the final rule benchmark against `data/splits/test.csv`.
3. **Rajiv (Zero-Shot Prompt Baseline):**
   - Use the test sentence IDs in `data/splits/test.csv` for the comparative zero-shot evaluation.
4. **Chaitu (Integration & Evaluation):**
   - In `evaluation/evaluate.py`, evaluate predictions strictly against `data/splits/test.csv`.
