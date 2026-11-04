from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.integration.pipeline import (
    analyze_text,
    analyze_document,
    demo_mode_label,
)
from src.integration.evaluation import (
    evaluate_predictions,
    make_demo_predictions,
)

app = FastAPI(
    title="Clarity Lint API",
    description="Python integration bridge for the Clarity Lint dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Clarity Lint API",
        "integration": "connected",
    }

@app.get("/api/status")
def integration_status():
    return {
        "status": "ok",
        "demo_label": demo_mode_label(),
        "modules": {
            "pipeline": "available",
            "evaluation": "available",
        },
        "note": "Optional team modules may still use demo fallbacks.",
    }

@app.post("/api/analyze")
def analyze(request: TextRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        result = analyze_text(text)
        return {
            "success": True,
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Text analysis failed: {str(exc)}",
        )

@app.post("/api/document")
def document_review(request: TextRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Document cannot be empty.")

    try:
        result = analyze_document(text)
        return {
            "success": True,
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document analysis failed: {str(exc)}",
        )

@app.post("/api/evaluate")
async def evaluate(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Upload a CSV file.",
        )

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        if "gold_label" not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain a gold_label column.",
            )

        prediction_columns = [
            col for col in ["rules_pred", "model_pred", "prompt_pred"]
            if col in df.columns
        ]

        if not prediction_columns:
            raise HTTPException(
                status_code=400,
                detail="No recognized prediction columns found.",
            )

        _, reports = evaluate_predictions(df, prediction_columns)

        return {
            "success": True,
            "data_source": "uploaded_evaluation_csv",
            "synthetic": False,
            "examples": len(df),
            "reports": reports,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation failed: {str(exc)}",
        )

@app.get("/api/evaluation/demo")
def evaluation_demo():
    return {
        "success": True,
        "data_source": "synthetic_demo_fixture",
        "synthetic": True,
        "warning": "Illustrative data only. Not measured project performance.",
        "reports": make_demo_predictions(),
    }
