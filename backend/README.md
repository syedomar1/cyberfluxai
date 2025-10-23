This backend contains enhanced reporting utilities for CyberFluxAI.

To enable RAG, detector training, SHAP explanations, and CTGAN augmentation, install optional dependencies:

pip install -r requirements.txt

Notes:

- sentence-transformers + faiss-cpu are used for building an embeddings index.
- shap and xgboost are used for detector explainability and modeling.
- ctgan (SDV) is used for synthetic data augmentation.

Quick example (from backend folder):

python -m reports.example_usage

Unit tests (requires pytest):

pytest tests/test_faithfulness.py
