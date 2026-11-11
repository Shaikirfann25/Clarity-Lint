# Clarity Lint - Integration Demo Script (4 minutes)

## 0:00-0:30 - Introduce the problem

Clarity Lint identifies possible ambiguity in requirements,
contracts, and policy documents.

It is a writing assistant, not a legal decision-maker.

## 0:30-1:15 - Live sentence analysis

Open Analyze Text.

Input:
"The admin monitors the user with the sensor."

Demonstrate:
- Genuine rule-based ambiguity detection.
- Explanation of competing interpretations.
- Suggested rewrites.
- Explicit component availability.

The current workspace cannot load DistilBERT because trained
checkpoint weights are missing. Do not describe its placeholder
output as a real prediction.

## 1:15-2:00 - Document review

Open Document Review.

Demonstrate:
- Sentence count.
- Flagged sentence count.
- Ambiguity category breakdown.
- Project-defined ambiguity rate.

Explain that ambiguity rate is descriptive, not a validated
legal-risk score.

## 2:00-3:00 - Evaluation lab

Open Evaluation Lab.

The frozen test set contains 76 examples.

The current evidence-aware report includes:
- Fresh rule predictions for all 76 examples.
- A direct comparison between rules and valid cached Gemini
  predictions on the same 74 examples.
- Two excluded Gemini responses that failed with HTTP 429.
- Cached DistilBERT predictions retained for provenance only,
  not scored because checkpoint weights are unavailable.

Discuss:
- Accuracy.
- Macro precision, recall, and F1.
- Per-class precision, recall, F1, and support.
- Confusion matrices.
- Latency provenance and limitations.

Do not claim Gemini was run live during this demonstration.
Do not claim DistilBERT was successfully evaluated.

## 3:00-4:00 - Limitations and conclusion

Discuss:
- Missing DistilBERT checkpoint weights.
- No configured live Gemini API in the audited environment.
- Heuristic rule limitations.
- Invalid external API responses.
- Dataset and annotation limitations.
- Need for human review.

Use observed errors from the frozen evaluation output when
discussing mistakes. The Error Analysis page currently includes
illustrative templates, not verified error examples.

Never present synthetic fixtures as measured results.
Never tune methods using the frozen test set.
