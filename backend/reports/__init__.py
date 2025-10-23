"""reports package

This package is intentionally light at import time. Heavy optional modules (RAG, CTGAN,
SHAP, XGBoost) are imported only where needed to avoid import-time failures when
optional dependencies are not installed.
"""

__all__ = [
	# import specific helpers directly from their modules to avoid heavy imports here
]
