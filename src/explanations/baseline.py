"""Zero-shot prompt baseline using Google Gemini.

Classifies each sentence into one of five ambiguity labels using a
documented, zero-shot prompt with temperature 0.  The prompt includes
label definitions and requires strict JSON output.

Note on baseline CSV generation:
--------------------------------
The packaged baseline predictions file (outputs/prompt_baseline_predictions.csv)
was generated using mock mode (--mock) for deterministic offline testing and
schema validation without requiring an active Gemini API key. It should NOT
be presented as live Gemini predictions. For real Gemini predictions, set
GEMINI_API_KEY and run the CLI or predict_zero_shot without mock mode.

Usage (CLI)
-----------
    python -m src.explanations.baseline --split data/splits/test.csv \\
        --output outputs/prompt_baseline_predictions.csv

Environment
-----------
    GEMINI_API_KEY : str   — your Google Gemini API key (never hardcoded).

This module must NOT import Streamlit.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────────
ALLOWED_LABELS: set[str] = {
    "no_ambiguity", "vague", "attachment", "scope", "pronoun",
}

# Prompt version tag — update when the prompt text changes.
PROMPT_VERSION = "v1.0"

SYSTEM_PROMPT = """\
You are a linguistic-ambiguity classifier for requirements and policy text.

## Label definitions
- no_ambiguity : The sentence has one clear, measurable interpretation.
- vague        : A word or phrase lacks a measurable threshold (e.g. "soon", "appropriate").
- attachment   : A modifier or prepositional phrase could attach to more than
                 one part of the sentence, producing different meanings.
- scope        : A quantifier or negation could apply to different parts of
                 the sentence.
- pronoun      : A pronoun could refer to more than one entity.

## Output Format
Return ONLY a valid JSON object (no markdown code fences, no introductory or trailing text) with exactly these keys:
{
  "label": "<no_ambiguity | vague | attachment | scope | pronoun>",
  "span": "<the shortest exact substring that causes the ambiguity, or null>",
  "reason": "<one-sentence explanation of the ambiguity or why the sentence is clear>"
}

## Examples
Example 1:
Sentence: The admin monitors the user with the sensor.
{"label": "attachment", "span": "with the sensor", "reason": "The prepositional phrase can modify 'monitors' or 'user'."}

Example 2:
Sentence: The supplier should respond soon.
{"label": "vague", "span": "soon", "reason": "'Soon' does not specify a measurable timeframe."}

Example 3:
Sentence: The service must return HTTP 200 within 500 milliseconds.
{"label": "no_ambiguity", "span": null, "reason": "The requirement contains specific, measurable criteria."}

## Rules
- "span" must be an EXACT substring of the input sentence, or null.
- "label" must be one of the five exact labels above.
- Do NOT wrap the JSON in markdown code fences.
"""


# ── Prompt builder ────────────────────────────────────────────────────────

def build_user_prompt(sentence: str) -> str:
    """Build the user-turn content for a single sentence."""
    return f"Sentence: {sentence}"


# ── JSON parsing helpers ──────────────────────────────────────────────────

def strip_code_fences(text: str) -> str:
    """Remove optional ```json ... ``` or ``` ... ``` wrappers."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    m = re.match(
        r"^```(?:json)?\s*\n?(.*?)\n?\s*```$", text, re.DOTALL
    )
    if m:
        return m.group(1).strip()
    return text


def parse_llm_response(raw: str) -> dict[str, Any] | None:
    """Try to extract a JSON dict from the raw LLM text.

    Returns None if parsing fails entirely.
    """
    cleaned = strip_code_fences(raw)
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except (json.JSONDecodeError, TypeError):
        pass

    # Last resort: find the first { ... } in the text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except (json.JSONDecodeError, TypeError):
            pass

    return None


# ── Validation ────────────────────────────────────────────────────────────

def validate_prediction(
    parsed: dict[str, Any] | None,
    sentence: str,
) -> dict[str, Any]:
    """Validate and normalise a parsed prediction dict.

    Returns a dict with keys: label, span, confidence, reason, valid.
    Invalid predictions get ``label="no_ambiguity"`` and ``valid=False``.
    """
    fallback: dict[str, Any] = {
        "label": "no_ambiguity",
        "span": None,
        "confidence": None,
        "reason": "LLM output could not be validated.",
        "valid": False,
    }

    if parsed is None:
        return fallback

    label = parsed.get("label", "").strip().lower()
    if label not in ALLOWED_LABELS:
        fallback["reason"] = f"Invalid label from LLM: '{label}'."
        return fallback

    span = parsed.get("span")
    if span is not None:
        span = str(span).strip()
        if span == "" or span.lower() == "null":
            span = None
        elif span not in sentence:
            # Span is not an exact substring — drop it
            span = None

    reason = parsed.get("reason", "No reason provided.")
    if not isinstance(reason, str):
        reason = str(reason)

    return {
        "label": label,
        "span": span,
        "confidence": None,          # never invent confidence
        "reason": reason,
        "valid": True,
    }


# ── LLM caller ───────────────────────────────────────────────────────────

def call_gemini(sentence: str, *, model_name: str = "gemini-3.1-flash-lite") -> str:
    """Send *sentence* to Google Gemini and return the raw text response.

    Supports both the ``google-generativeai`` SDK and direct REST calls
    via ``requests`` when the SDK is not installed.
    Requires a valid ``GEMINI_API_KEY`` (or ``GOOGLE_API_KEY``) environment variable.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set.  "
            "Set it to your Google Gemini API key before running the baseline."
        )

    try:
        import google.generativeai as genai  # lazy import
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
        )

        response = model.generate_content(
            build_user_prompt(sentence),
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                max_output_tokens=256,
            ),
        )
        return response.text
    except ImportError:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "parts": [{"text": build_user_prompt(sentence)}]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 256
            }
        }
        max_retries = 3
        backoff = 2.0
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code in (429, 503) and attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise


def classify_sentence(
    sentence: str,
    *,
    llm_fn=None,
    model_name: str = "gemini-3.1-flash-lite",
) -> dict[str, Any]:
    """Classify a single sentence via the zero-shot prompt.

    Parameters
    ----------
    sentence : str
        The sentence to classify.
    llm_fn : callable or None
        Override for testing — a function(sentence) → str.
        When None, :func:`call_gemini` is used.
    model_name : str
        Gemini model name (ignored when *llm_fn* is provided).

    Returns
    -------
    dict
        Keys: label, span, confidence, reason, valid, source.
    """
    caller = llm_fn if llm_fn is not None else (
        lambda s: call_gemini(s, model_name=model_name)
    )

    try:
        raw = caller(sentence)
    except Exception as exc:
        clean_msg = re.sub(r"key=[^&\s\"']+", "key=[REDACTED]", str(exc))
        return {
            "label": "no_ambiguity",
            "span": None,
            "confidence": None,
            "reason": f"LLM call failed: {clean_msg}",
            "valid": False,
            "source": "prompt",
        }

    parsed = parse_llm_response(raw)
    result = validate_prediction(parsed, sentence)
    result["source"] = "prompt"
    return result


# ── Batch prediction (integration interface) ──────────────────────────────

def predict_zero_shot(
    sentences: list[str],
    *,
    llm_fn=None,
    model_name: str = "gemini-3.1-flash-lite",
    delay: float = 0.0,
    source: str = "prompt_baseline",
) -> list[dict[str, Any]]:
    """Predict ambiguity labels for a batch of sentences using zero-shot prompt.

    Each prediction in the returned list complies with the shared integration schema
    (docs/shared_schema.json and docs/integration_contract.md):
    - ``source``: "prompt_baseline"
    - ``label``: one of {"no_ambiguity", "vague", "attachment", "scope", "pronoun"}
    - ``span``: exact substring inside the sentence, or None
    - ``confidence``: None (confidence is never fabricated)
    - ``reason``: human-readable explanation of why the sentence was classified as such

    Parameters
    ----------
    sentences : list[str]
        A list of sentences to classify.
    llm_fn : callable or None, optional
        A callable(sentence) -> str for testing / offline execution.
        If None, calls the live Gemini API (requires GEMINI_API_KEY).
    model_name : str, optional
        Gemini model name to use when llm_fn is None (default: "gemini-2.0-flash").
    delay : float, optional
        Delay in seconds between successive LLM API calls for rate limiting (default: 0.0).
    source : str, optional
        Source identifier tag for schema integration (default: "prompt_baseline").

    Returns
    -------
    list[dict[str, Any]]
        List of detection dictionaries, one per input sentence, matching the shared schema.
    """
    if isinstance(sentences, str):
        sentences = [sentences]

    results: list[dict[str, Any]] = []
    for i, s in enumerate(sentences):
        sentence_str = str(s) if s is not None else ""
        classification = classify_sentence(
            sentence_str,
            llm_fn=llm_fn,
            model_name=model_name,
        )
        prediction = {
            "source": source,
            "label": classification["label"],
            "span": classification["span"],
            "confidence": None,
            "reason": classification["reason"],
        }
        results.append(prediction)

        if llm_fn is None and delay > 0 and i < len(sentences) - 1:
            time.sleep(delay)

    return results


# ── Batch runner ──────────────────────────────────────────────────────────

def run_baseline(
    df: pd.DataFrame,
    *,
    text_col: str = "text",
    label_col: str = "label",
    id_col: str = "sentence_id",
    llm_fn=None,
    model_name: str = "gemini-3.1-flash-lite",
    delay: float = 0.5,
) -> pd.DataFrame:
    """Run the prompt baseline on every row of *df*.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain *text_col* and *label_col*.
    llm_fn : callable or None
        Override for testing.
    delay : float
        Seconds to sleep between API calls (rate-limiting).

    Returns
    -------
    pd.DataFrame
        Columns: sentence_id, text, gold_label, prompt_pred, span,
        reason, valid.
    """
    rows: list[dict[str, Any]] = []
    invalid_count = 0

    for _, row in df.iterrows():
        sentence = str(row[text_col])
        result = classify_sentence(
            sentence, llm_fn=llm_fn, model_name=model_name,
        )

        if not result["valid"]:
            invalid_count += 1

        rows.append({
            "sentence_id": row.get(id_col, ""),
            "text": sentence,
            "gold_label": row[label_col],
            "prompt_pred": result["label"],
            "span": result["span"],
            "reason": result["reason"],
            "valid": result["valid"],
        })

        # Rate-limit real API calls (not mocked ones)
        if llm_fn is None and delay > 0:
            time.sleep(delay)

    out_df = pd.DataFrame(rows)

    if invalid_count:
        print(
            f"[baseline] {invalid_count}/{len(df)} predictions were invalid "
            f"and fell back to 'no_ambiguity'.",
            file=sys.stderr,
        )

    return out_df


# ── CLI entry point ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Clarity Lint zero-shot prompt baseline."
    )
    parser.add_argument(
        "--split",
        default="data/splits/test.csv",
        help="Path to the input split CSV (default: test split).",
    )
    parser.add_argument(
        "--output",
        default="outputs/prompt_baseline_predictions.csv",
        help="Path for the output predictions CSV.",
    )
    parser.add_argument(
        "--model",
        default="gemini-3.1-flash-lite",
        help="Gemini model name.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds between API calls (rate-limiting).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run with offline simulated LLM for testing pipeline without an API key.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.split)
    print(f"[baseline] Loaded {len(df)} sentences from {args.split}")
    print(f"[baseline] Model: {args.model}  |  Prompt version: {PROMPT_VERSION}")

    mock_fn = None
    if args.mock:
        print("[baseline] Running in mock offline mode (no API key required).")
        def _mock_caller(sentence: str) -> str:
            low = sentence.lower()
            if any(term in low for term in ["soon", "appropriate", "regularly", "quickly", "reasonable", "timely"]):
                return json.dumps({"label": "vague", "span": "soon", "reason": "Term lacks measurable threshold."})
            elif "with the " in low or "with a " in low:
                return json.dumps({"label": "attachment", "span": "with the sensor", "reason": "Prepositional phrase attachment."})
            elif any(p in low.split() for p in ["she", "he", "they", "it", "her", "his", "them"]):
                return json.dumps({"label": "pronoun", "span": "she", "reason": "Multiple candidate antecedents."})
            elif "not " in low or "all " in low or "every " in low:
                return json.dumps({"label": "scope", "span": "not", "reason": "Quantifier or negation scope."})
            return json.dumps({"label": "no_ambiguity", "span": None, "reason": "Clear sentence."})
        mock_fn = _mock_caller

    result_df = run_baseline(
        df, llm_fn=mock_fn, model_name=args.model, delay=args.delay,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_path, index=False)
    print(f"[baseline] Wrote {len(result_df)} predictions to {out_path}")

    # Quick summary
    if "gold_label" in result_df.columns and "prompt_pred" in result_df.columns:
        matches = (result_df["gold_label"] == result_df["prompt_pred"]).sum()
        total = len(result_df)
        print(f"[baseline] Accuracy (quick check): {matches}/{total} "
              f"= {matches/total:.2%}")

    valid_pct = result_df["valid"].sum() / len(result_df) * 100
    print(f"[baseline] Valid predictions: {valid_pct:.1f}%")


if __name__ == "__main__":
    main()

