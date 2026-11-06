# src/model/__init__.py
# Makes src/model a proper Python package.
# Exposes the public inference interface.
from src.model.predict import predict

__all__ = ["predict"]

