import sys
import os
import pytest

# Ensure backend package is importable when running tests from the backend/ folder
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from reports.faithfulness import compute_simple_faithfulness, compute_detailed_faithfulness


def test_simple_ip_check():
    rows = [{"src": "1.2.3.4", "dst": "5.6.7.8"}]
    llm = {"summary": "Connection from 1.2.3.4 to 9.9.9.9"}
    r = compute_simple_faithfulness(llm, rows)
    assert r["ips_claimed"]
    assert r["ips_verified"] == 1


def test_detailed_returns_report():
    rows = [{"src": "1.1.1.1", "Bytes_int": 100}, {"src": "2.2.2.2", "Bytes_int": 200}]
    llm = {"summary": "There are 2 flows and total bytes 300"}
    r = compute_detailed_faithfulness(llm, rows)
    assert "aggregates" in r
    assert r["aggregates"].get("n_rows") == 2
