"""Small example demonstrating faithfulness checks and (if available) RAG retrieval.

This script is safe to run even if optional deps are missing; it will skip heavy parts.
"""
from .faithfulness import compute_detailed_faithfulness


def main():
    # minimal evidence
    rows = [
        {"src": "10.0.0.1", "dst": "10.0.0.2", "Bytes_int": 1500, "Duration_sec": 2},
        {"src": "10.0.0.3", "dst": "8.8.8.8", "Bytes_int": 50000, "Duration_sec": 30},
    ]

    llm_output = {"summary": "Host 10.0.0.1 sent 1500 bytes to 10.0.0.2 and 10.0.0.3", "recommendations": []}

    report = compute_detailed_faithfulness(llm_output, rows)
    print("Faithfulness report:", report)

    try:
        # Lazy-import RAG only if optional deps are available
        from .rag import build_index, retrieve_rows
        idx, meta = build_index(rows)
        res = retrieve_rows("suspicious bytes", idx, meta, k=2)
        print("RAG results:", res)
    except Exception as e:
        print("RAG skipped (missing deps):", e)


if __name__ == "__main__":
    main()
