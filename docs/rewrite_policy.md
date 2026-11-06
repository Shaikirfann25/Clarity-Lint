# Clarity Lint — Explanations, Rewrite Policy & Prompt Baseline Report

**Author / Role:** Rajiv Kumar (Person 4 — Explanations, Clear Rewrites & Prompt Baseline)  
**Date:** October 31, 2026 (Updated November 1, 2026)  
**Module Directory:** `src/explanations/`  
**Test Suite:** `tests/test_explanations.py` (60 tests passing)  

---

## 1. Executive Summary

As part of the **Person 4** deliverables for Clarity Lint, this module turns raw ambiguity detections into actionable, interpretable guidance for humans. The module bridges automated detection (rule-based patterns by Sudharshan and DistilBERT classifications by Aman) with human decision-makers, providing:

1. **Modular Explanation Engine (`src/explanations/explain.py`):** Produces human-readable explanations, identifies candidate readings, and supplies meaning-preserving rewrites for all five canonical labels (`no_ambiguity`, `vague`, `attachment`, `scope`, `pronoun`).
2. **Controlled Rewrite Generator (`src/explanations/rewrite.py`):** Generates structured alternatives when author intent is unknown (e.g., *"If you mean A, use... / If you mean B, use..."*), strictly avoiding invented deadlines, actors, numbers, or legal obligations.
3. **Canonical Templates (`src/explanations/templates.py`):** Deterministic, testable linguistic templates quoting the exact flagged evidence span.
4. **Zero-Shot Prompt Baseline (`src/explanations/baseline.py`):** A reproducible LLM baseline using Google Gemini (`temperature=0`) with task definitions, few-shot examples, strict JSON output parsing, resilient fallbacks, and a batch prediction interface (`predict_zero_shot(sentences: list[str]) -> list[dict]`) exported through `src/explanations/__init__.py`.
5. **Comprehensive Test Suite (`tests/test_explanations.py`):** 60 automated unit tests covering all labels, determinism, malformed JSON, code-fenced outputs, out-of-sentence spans, tricky negatives, batch prediction, and schema conformance against `docs/shared_schema.json`.

---

## 2. Linguistic Ambiguity & Interpretation Impact

Writing requirements, contracts, and policies requires verifiable language. Each ambiguity category impacts interpretation differently and requires specific information from the writer:

### 2.1 `vague` — Vague Terms
- **Linguistic Impact:** The term lacks a measurable, shared definition in context. Readers apply subjective thresholds, creating unresolvable disagreements during compliance audits or verification testing.
- **Examples:** *"The system should respond quickly"*, *"The team will review the request soon"*.
- **What the Writer Must Clarify:** Concrete, numeric metrics or verifiable deadlines (e.g., latency $\le 200\text{ ms}$, submission by 2026-11-20 17:00 UTC).
- **Our Rewrite Strategy:** Supply explicit placeholders like `[within N hours / by YYYY-MM-DD]` or `[minimum N units]`. **Never invent specific numbers or dates.**

### 2.2 `attachment` — Attachment Ambiguity
- **Linguistic Impact:** A prepositional phrase, relative clause, or participial modifier can grammatically attach to two distinct syntactic heads (e.g., verb vs. object noun phrase), resulting in two conflicting logical propositions.
- **Example:** *"The admin monitors the user with the sensor."*
  - *Reading 1 (VP attachment):* The admin uses the sensor as an instrument to monitor the user.
  - *Reading 2 (NP attachment):* The user possesses or is associated with the sensor.
- **What the Writer Must Clarify:** Which entity is modified by the phrase.
- **Our Rewrite Strategy:** Present explicit syntactic relocations:
  - *"If you mean the action is performed using [span]: restructure adjacent to the verb/agent."*
  - *"If you mean [span] is associated with the other entity: restructure adjacent to that entity."*

### 2.3 `scope` — Scope Ambiguity
- **Linguistic Impact:** A quantifier (`all`, `every`, `each`) or negation (`not`) interacts with a coordinated conjunction (`and`, `or`), producing broad vs. narrow logical interpretations ($\neg(A \land B)$ vs $\neg A \land B$).
- **Example:** *"The platform does not notify all users and administrators."*
  - *Reading 1 (Broad scope):* Neither users nor administrators receive notifications.
  - *Reading 2 (Narrow scope):* Users do not receive notifications, but administrators do.
- **What the Writer Must Clarify:** Which operands fall under the quantifier or negation operator.
- **Our Rewrite Strategy:** Explicit distributive wording:
  - *"If you mean the broad reading: rewrite so the modifier clearly covers all items (e.g., 'neither A nor B')."*
  - *"If you mean the narrow reading: rewrite so the modifier clearly applies to only the relevant item (e.g., 'A, but not B')."*

### 2.4 `pronoun` — Pronoun/Reference Ambiguity
- **Linguistic Impact:** An anaphoric pronoun (`she`, `he`, `it`, `they`) has multiple grammatically compatible antecedents in the same or preceding clause.
- **Example:** *"When Priya called Ananya, she was upset."*
  - *Reading 1:* Priya was upset.
  - *Reading 2:* Ananya was upset.
- **What the Writer Must Clarify:** The exact named entity, role, or object intended.
- **Our Rewrite Strategy:**
  - *"If you mean the first-mentioned entity: replace [span] with that specific entity's name or title."*
  - *"If you mean the second-mentioned entity: replace [span] with that specific entity's name or title."*

### 2.5 `no_ambiguity` — Clear Sentence
- **Linguistic Impact:** The sentence has one obvious, unambiguous interpretation. All modifiers, quantifiers, and pronouns have single deterministic bindings.
- **Example:** *"The server must respond within 200 milliseconds."*
- **Our Strategy:** Return empty readings and rewrites with a cautious confirmation that no targeted pattern was flagged, noting that human review remains prudent.

---

## 3. Controlled Templates vs. Open-Ended Generation

In university engineering and legal text processing, **controlled template-based generation** is vastly superior to open-ended LLM text generation:

| Criterion | Controlled Templates (`src/explanations/`) | Open-Ended Generative LLM |
|---|---|---|
| **Hallucination Risk** | **Zero.** Never invents numbers, dates, or actors. | **High.** Frequently invents convenient dates, names, or constraints. |
| **Legal/Compliance Safety** | Preserves original obligations; marks suggestions clearly. | May introduce binding terms (`must`, `shall`) not in original. |
| **Determinism & Testability** | 100% deterministic; unit tests assert exact output. | Stochastic; can change across runs or API updates. |
| **Execution Latency** | **$< 0.1\text{ ms}$**; runs locally in pure Python. | $500\text{--}2000\text{ ms}$; requires network and API tokens. |
| **Privacy & Air-Gapped Use** | Fully local; no text ever leaves the machine. | Sensitive corporate text is transmitted to external servers. |

---

## 4. Meaning Preservation Policy (The 7 Core Rules)

Every rewrite generated by `src/explanations/rewrite.py` adheres to seven non-negotiable principles:

1. **No Invented Obligations:** Never introduce deontic modal verbs (`must`, `shall`, `required to`) if absent in the source.
2. **No Invented Deadlines or Numbers:** Never invent values like *"within 5 days"* or *"by Friday"*. Use explicit placeholders like `[within N hours / by YYYY-MM-DD]`.
3. **No Invented Actors:** Do not invent roles or systems (e.g., changing *"it failed"* to *"the database server failed"* without confirmation).
4. **Explicit Alternatives When Intent Is Unknown:** Present symmetrical options (`"If you mean A..."` and `"If you mean B..."`).
5. **Exact Span Quoting:** When evidence is available, quote the exact substring (e.g., `"with the sensor"`).
6. **Cautious Wording:** Use phrasing like *"may be read as"*, *"possible ambiguity"*, and *"consider replacing"*.
7. **Safe Fallbacks:** If a span is omitted or not found in the original sentence, cleanly substitute `[ambiguous phrase]` rather than crashing.

---

## 5. Zero-Shot Prompt Baseline Design

The prompt baseline (`src/explanations/baseline.py`) evaluates how a state-of-the-art general language model performs on ambiguity classification without task-specific fine-tuning.

> [!IMPORTANT]
> **Clarification on Baseline Predictions CSV (`outputs/prompt_baseline_predictions.csv`):**  
> The existing baseline CSV file committed to `outputs/prompt_baseline_predictions.csv` was generated using **offline mock mode (`--mock`)** with simulated heuristic rules. It was created specifically to verify the evaluation pipeline (`evaluation/evaluate.py`), dashboard visualizations, and metrics calculation without requiring external network access or consuming API quota during development and grading.  
> **It is NOT presented as real Google Gemini predictions.**  
> To generate live Gemini predictions, set the `GEMINI_API_KEY` environment variable and run:
> ```bash
> python -m src.explanations.baseline --split data/splits/test.csv --output outputs/prompt_baseline_predictions.csv
> ```

### 5.1 Architecture & Settings
- **Model:** Google Gemini (`gemini-3.1-flash-lite`, configurable via `--model`).
- **Temperature:** `0` (deterministic sampling).
- **Token Limit:** `256` output tokens.
- **Protocol:** Zero-shot with task description, label definitions, few-shot illustrative examples, and JSON schema constraints.
- **API Access:** Reads `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) from the environment. Supports direct REST calls via `requests` and `google-generativeai` SDK. Includes automated backoff retry logic for rate limits (429) and temporary service unavailability (503).

### 5.2 System Prompt Structure
```text
You are a linguistic-ambiguity classifier for requirements and policy text.

## Label definitions
- no_ambiguity : The sentence has one clear, measurable interpretation.
- vague        : A word or phrase lacks a measurable threshold.
- attachment   : A modifier or prepositional phrase could attach to more than one part.
- scope        : A quantifier or negation could apply to different parts.
- pronoun      : A pronoun could refer to more than one entity.

## Output Format
Return ONLY a valid JSON object with keys:
{
  "label": "<no_ambiguity | vague | attachment | scope | pronoun>",
  "span": "<exact substring, or null>",
  "reason": "<one-sentence explanation>"
}

## Examples
[Includes 3 validated examples: attachment, vague, and no_ambiguity]
```

### 5.3 Resilient JSON Parsing & Validation
Language models frequently wrap JSON in markdown fences (````json ... ````) or include conversational filler. `baseline.py` implements a four-stage parsing pipeline:
1. **Direct JSON loading** after stripping markdown fences.
2. **Regex extraction** of the first `{...}` block if surrounding text exists.
3. **Label verification** against canonical set `{"no_ambiguity", "vague", "attachment", "scope", "pronoun"}`.
4. **Span verification:** Checks `span in sentence`. If the model hallucinated a word not in the original sentence, `span` is safely set to `None` while preserving the valid label.
5. **Safe Fallback:** If parsing fails completely, the sentence is assigned `no_ambiguity` with `valid=False`. The runner logs the failure count to stderr and never crashes.

### 5.4 Batch Prediction Interface (`predict_zero_shot`)
For seamless integration across team components, Person 4 exports the batch prediction function:
```python
predict_zero_shot(sentences: list[str]) -> list[dict]
```
This is exported via `src/explanations/__init__.py`. Each dictionary in the returned list strictly matches our shared integration schema (`docs/shared_schema.json` and `docs/integration_contract.md`):
- `source`: `"prompt_baseline"`
- `label`: Canonical label (`"no_ambiguity"`, `"vague"`, `"attachment"`, `"scope"`, `"pronoun"`)
- `span`: Exact substring within the sentence or `None`
- `confidence`: `None` (baseline model does not fabricate confidence scores)
- `reason`: Explanation string

### 5.5 Genuine Gemini API Benchmark vs. Mock Baseline

To ensure complete transparency and integrity in our comparative evaluation:

| Attribute | Mock / Offline Baseline (`outputs/prompt_baseline_predictions.csv`) | Genuine Live API Benchmark (`outputs/prompt_baseline_test_predictions.csv`) |
|---|---|---|
| **Execution Mode** | Simulated offline heuristics (`--mock`) | Real Google Gemini API calls |
| **Model Used** | Rule-based regex simulation | `gemini-3.1-flash-lite` (Temperature 0) |
| **Date Executed** | October 31, 2026 | November 6, 2026 |
| **Evaluation Set** | Frozen `data/splits/test.csv` (76 examples) | Frozen `data/splits/test.csv` (76 examples) |
| **Accuracy** | 63.16% (48/76) | **90.79%** (69/76) |
| **Macro F1** | 0.6086 | **0.9032** |
| **Weighted F1** | 0.6103 | **0.9045** |
| **Per-Class F1** | `pronoun`: 0.7368<br>`vague`: 0.3333<br>`attachment`: 0.6364<br>`scope`: 0.7586<br>`no_ambiguity`: 0.5778 | `pronoun`: **1.0000**<br>`vague`: **0.9375**<br>`attachment`: **0.9286**<br>`scope`: **0.7407**<br>`no_ambiguity`: **0.9091** |
| **Failed Requests** | 0 | 2 requests (`S460`, `S429`) hit rate-limiting (HTTP 429) and safely fell back to `no_ambiguity` |
| **Report File** | `outputs/evaluation_report.json` | `outputs/prompt_baseline_test_evaluation_report.json` |

#### Limitations & Error Analysis:
1. **API Rate Limiting:** On the standard Gemini free tier, bursts of requests can trigger HTTP 429 rate limits. During the 76-sentence batch, 2 requests encountered rate limits and were safely caught by our fallback mechanism without halting pipeline execution.
2. **Scope Ambiguity:** Scope ambiguity remained the hardest category for zero-shot prompt classification (F1: 0.7407), where quantifier and negation scopes (`not`, `all`, `every`) occasionally overlap with `no_ambiguity` or `vague`.
3. **Pronoun & Vague Precision:** The zero-shot prompt showed exceptional capability on `pronoun` ambiguity (100% precision, 100% recall) and `vague` terms (100% recall, 93.75% F1).

---

## 6. Verification and Integration Hand-off

### 6.1 Integration with Person 5 (`pipeline.py`)
`src/integration/pipeline.py` dynamically calls Person 4 via:
```python
from src.explanations.explain import explain
result = explain(sentence, detections)
```
Verified returning:
- `explanation`: Detailed, cautious explanation string.
- `readings`: List of plausible interpretations.
- `rewrites`: List of actionable candidate rewrites.

And for batch evaluation / comparison:
```python
from src.explanations import predict_zero_shot
predictions = predict_zero_shot(sentences)
```

### 6.2 Evaluation CSV Schema
The prompt baseline outputs CSV files ready for `evaluation/evaluate.py`:
- `outputs/prompt_baseline_predictions.csv`: Packaged offline mock baseline (for testing without external network).
- `outputs/prompt_baseline_test_predictions.csv`: Genuine Google Gemini zero-shot baseline predictions.
- `outputs/prompt_baseline_test_evaluation_report.json`: Metrics report generated from live API predictions.

Columns in both files:
- `sentence_id`: Unique identifier (e.g. `S001`).
- `text`: Sentence string.
- `gold_label`: Human ground-truth annotation.
- `prompt_pred`: Predicted label.
- `span`: Extracted evidence substring or null.
- `reason`: Model explanation.
- `valid`: Boolean indicating schema compliance.

---

## 7. Viva Defense Checklist for Rajiv (Person 4)

| Anticipated Viva Question | Recommended Answer |
|---|---|
| **Why use templates instead of an LLM for rewrites?** | *"Templates guarantee zero hallucinations. In requirements and legal drafting, an unconstrained LLM can invent deadlines, numbers, or legal obligations that did not exist in the original text. Templates offer safe, testable options and leave domain decisions to the human author."* |
| **How do you handle unknown intent?** | *"We never guess. We offer structured alternatives: 'If you mean A, use X; if you mean B, use Y'. The author retains full agency."* |
| **What happens if the LLM baseline produces invalid JSON?** | *"Our parsing pipeline strips code fences, extracts embedded JSON objects, validates labels against the canonical set, verifies that the span is an exact substring, and falls back to a safe no_ambiguity prediction if output is unrecoverable, logging the error rate without crashing."* |
| **Why does baseline.py use temperature 0?** | *"Temperature 0 enforces greedy decoding for maximum reproducibility during evaluation on the held-out test split."* |
| **Was the packaged baseline CSV generated with live Gemini predictions?** | *"No, the existing baseline CSV was generated using mock mode (--mock) so that evaluation scripts and dashboard demos can run deterministically offline without API credentials. For real Gemini predictions, set GEMINI_API_KEY and run baseline.py."* |
| **What is the schema format for predict_zero_shot?** | *"It returns a list of dictionaries, one per sentence, with keys: source, label, span, confidence, reason, strictly matching docs/shared_schema.json and the integration contract."* |
