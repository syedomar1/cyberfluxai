"""RAG helpers: build embeddings index over evidence rows and retrieve relevant rows.

Uses sentence-transformers + faiss-cpu. Exposes:
 - build_index(rows, model_name='all-MiniLM-L6-v2') -> index, metadata
 - retrieve_rows(query, index, metadata, model_name, k=5) -> list[rows]
"""
from typing import List, Dict, Any, Tuple

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
except Exception:
    SentenceTransformer = None
    faiss = None
    np = None


def _row_to_text(row: Dict) -> str:
    # Join key fields to create an evidence text
    keys = ["ts", "src", "dst", "protocol", "Bytes_int", "Duration_sec"]
    parts = []
    for k in keys:
        if k in row and row.get(k) is not None:
            parts.append(f"{k}:{row.get(k)}")
    return " | ".join(parts)


def build_index(rows: List[Dict], model_name: str = "all-MiniLM-L6-v2") -> Tuple[Any, List[Dict]]:
    """Build FAISS index from list of row dicts. Returns (index, metadata list).

    metadata is the original rows in the same order as vectors in the index.
    """
    if SentenceTransformer is None or faiss is None or np is None:
        raise RuntimeError("sentence-transformers, faiss-cpu and numpy are required to build index")

    texts = [_row_to_text(r) for r in rows]
    model = SentenceTransformer(model_name)
    vectors = model.encode(texts, show_progress_bar=False)
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype('float32'))
    return index, rows


def retrieve_rows(query: str, index: Any, metadata: List[Dict], model_name: str = "all-MiniLM-L6-v2", k: int = 5) -> List[Dict]:
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is required for retrieval")
    model = SentenceTransformer(model_name)
    qv = model.encode([query])
    D, I = index.search(qv.astype('float32'), k)
    results = []
    for idx in I[0]:
        if idx < 0 or idx >= len(metadata):
            continue
        results.append(metadata[idx])
    return results
