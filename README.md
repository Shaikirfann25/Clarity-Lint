# Clarity Lint — Imperial Jade Edition
**Person 5: Dashboard, Integration & Evaluation**

A polished Streamlit integration workbench for the Clarity Lint NLP project. Visual direction: aged jade, antique imperial gold, parchment-like typography, engraved details. The app includes a transparent demo fallback and integration adapters for teammates' modules.

> **Important:** Demo heuristics and evaluation fixtures are illustrative only. They are not trained-model results, legal advice, or evidence of measured performance. Replace them with the team's actual outputs before the final presentation.

## 1. Requirements
- Python 3.10+ (Python 3.11 recommended)
- pip
- Teammates' modules/data are optional for demo mode and required for real end-to-end evaluation.

## 2. Setup (Windows PowerShell)
```powershell
cd Clarity_Lint_Imperial_Jade
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app/app.py
```
If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Run tests
```powershell
python -m pytest -q
```

## 4. Pages
- **Overview:** project pipeline and scope.
- **Analyze Text:** sentence analysis, evidence, explanations, candidate rewrites, JSON export.
- **Document Review:** UTF-8 `.txt` upload/paste, sentence summary, type breakdown, CSV export.
- **Evaluation Lab:** calculate reports from an uploaded prediction CSV; synthetic fixtures are clearly labeled.
- **Error Analysis:** editable failure log template and export.
- **Integration Status:** shared schema and expected module paths.
- **Viva & Demo:** demo script and viva answers.

## 5. Shared label schema
Use exactly:
`no_ambiguity`, `vague`, `attachment`, `scope`, `pronoun`

Recommended record:
```json
{
  "sentence_id": "S001",
  "text": "The admin monitors the user with the sensor.",
  "gold_label": "attachment",
  "predictions": [
    {
      "source": "rules",
      "label": "attachment",
      "span": "with the sensor",
      "confidence": null,
      "reason": "The phrase may attach in more than one way."
    }
  ],
  "readings": [
    "The admin uses a sensor to monitor the user.",
    "The user has a sensor associated with them."
  ],
  "rewrites": ["The admin uses the sensor to monitor the user."]
}
```

## 6. Connect teammates' code
The integration adapter in `src/integration/pipeline.py` attempts these imports:
- `src.rules.detect.detect([sentence])` — Person 2
- `src.model.predict.predict([sentence])` — Person 3
- `src.explanations.explain.explain(sentence, detections)` — Person 4

The current fallback intentionally reports `demo_fallback`. Adjust the adapter if a teammate's function signature differs. Do not edit their core module to fit the UI; coordinate a stable contract instead. The model output is kept separate from rule output so disagreement is not hidden.

For real evaluation, export one row per fixed test sentence with columns:
- `sentence_id`
- `gold_label`
- `rules_pred`
- `model_pred`
- `prompt_pred`

All methods must use the same test IDs and label mapping. Use train for fitting, dev for choices/thresholds, and test only for final evaluation.

## 7. Project-defined ambiguity rate
`flagged sentences / total sentences * 100`. This is a descriptive dashboard statistic, **not** an established legal-risk score. A missing flag does not prove a sentence is clear.

## 8. Person 5 deliverables
- `app/app.py`
- `src/integration/` adapters and normalization
- `evaluation/` metrics and error-analysis workflow
- tests and shared schema
- reproducible run instructions and demo script

## 9. Limitations
- The bundled demo detector uses simple patterns and will miss context-dependent cases and may produce false positives.
- Sentence splitting is lightweight and not a substitute for a validated NLP sentence segmenter.
- No DistilBERT checkpoint is bundled.
- Demo fixtures are synthetic and must never be reported as measured model performance.
- Rewrites are candidates; intended meaning must be confirmed by a human.

## One-click-ish Windows launch
From the extracted project folder, double-click `scripts/run_windows.bat`. It creates the virtual environment if missing, installs requirements, and starts Streamlit. Internet access is required for package installation.

## Evaluation demo CSV
`data/demo/sample_predictions_ILLUSTRATIVE.csv` can be uploaded to the Evaluation Lab to check the comparison interface. The rows are intentionally illustrative, not a real dataset or measured result. Do not include these scores in the final report.
