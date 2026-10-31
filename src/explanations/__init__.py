"""Explanations, rewrites, and prompt-baseline module for Clarity Lint.

Public API
----------
explain(sentence, detections)  →  dict with explanation, readings, rewrites
rewrite(sentence, label, span) →  list[str]
"""
from src.explanations.explain import explain
from src.explanations.rewrite import rewrite

__all__ = ["explain", "rewrite"]

