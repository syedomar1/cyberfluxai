# backend/reports/utils.py
"""
Utilities for CyberFluxAI report generation.

Provides:
 - load_logs_csv(filename, nrows) -> pd.DataFrame
 - compute_basic_metrics(df, date_col_candidates) -> dict
 - sample_evidence_rows(df, k) -> list[dict]

Place logs.csv in backend/data/ or pass an absolute path to functions that accept filename.
"""
import os
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime

# default data directory (backend/data)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)


def load_logs_csv(filename: str = "logs.csv", nrows: Optional[int] = None, parse_dates: bool = True) -> pd.DataFrame:
    """
    Safely load a CSV containing logs.
    - filename: either an absolute path or a file name located in backend/data/
    - nrows: optional integer to limit rows (useful for dev/testing)
    - parse_dates: attempt to parse a likely timestamp column
    Returns a pandas.DataFrame with trimmed column names.
    Raises FileNotFoundError if file not found.
    """
    # allow absolute paths or filenames relative to DATA_DIR
    path = filename if os.path.isabs(filename) else os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found at: {path}. Place your CSV in {DATA_DIR} or pass a full path.")

    # Use python engine to let pandas infer separator if unusual
    df = pd.read_csv(path, engine="python", nrows=nrows)
    # normalize column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]

    # attempt to parse a likely date column
    if parse_dates:
        for cand in ["Date first seen", "Date", "timestamp", "time", "datetime"]:
            if cand in df.columns:
                try:
                    df[cand] = pd.to_datetime(df[cand], errors="coerce")
                except Exception:
                    # quietly ignore parse failures (leave column as-is)
                    pass
                break

    return df


def compute_basic_metrics(df: pd.DataFrame, date_col_candidates: Optional[List[str]] = None) -> Dict:
    """
    Compute lightweight summary metrics to display and optionally pass to LLM.
    Returns JSON-serializable dict:
      {
        total_rows, unique_attack_types, suspicious_rows,
        top_attack_types (dict), top_src_ips (dict), top_dst_ips (dict),
        date_column (str or None), timeline_sample (dict)
      }
    """
    if date_col_candidates is None:
        date_col_candidates = ["Date first seen", "Date", "timestamp", "time", "datetime"]

    metrics: Dict = {}
    metrics["total_rows"] = int(len(df))
    metrics["unique_attack_types"] = int(df["attackType"].nunique()) if "attackType" in df.columns else 0

    if "class" in df.columns:
        try:
            metrics["suspicious_rows"] = int((df["class"].astype(str).str.lower() != "normal").sum())
        except Exception:
            metrics["suspicious_rows"] = 0
    else:
        metrics["suspicious_rows"] = 0

    metrics["top_attack_types"] = df["attackType"].fillna("unknown").value_counts().head(10).to_dict() if "attackType" in df.columns else {}
    metrics["top_src_ips"] = df["Src IP Addr"].value_counts().head(10).to_dict() if "Src IP Addr" in df.columns else {}
    metrics["top_dst_ips"] = df["Dst IP Addr"].value_counts().head(10).to_dict() if "Dst IP Addr" in df.columns else {}

    # pick first available date column
    metrics["date_column"] = None
    for c in date_col_candidates:
        if c in df.columns:
            metrics["date_column"] = c
            break

    # timeline sample (resample to hourly if datetime present)
    metrics["timeline_sample"] = {}
    if metrics["date_column"] is not None:
        try:
            s = pd.to_datetime(df[metrics["date_column"]], errors="coerce")
            timeline = s.dropna().dt.floor("H").value_counts().sort_index()
            # keep last up to 48 points for compactness
            timeline = timeline.tail(48)
            # convert index datetimes to ISO strings
            metrics["timeline_sample"] = {str(k): int(v) for k, v in timeline.to_dict().items()}
        except Exception:
            metrics["timeline_sample"] = {}

    return metrics


def sample_evidence_rows(df: pd.DataFrame, k: int = 8) -> List[Dict]:
    """
    Return a list of evidence dictionaries (k rows) with compact fields for PDF/LLM.

    Strategy:
      - if numeric bytes column exists (named '_bytes_num' or 'Bytes'), sample top flows by bytes
      - else return the first k rows
    Each dict:
      { time, src, dst, proto, bytes, packets, attackType, raw }
    """
    # ensure we operate on copy to avoid side effects
    working = df.copy()

    # helper to safely extract fields
    def _val(row, key):
        return row.get(key, "") if key in row.index else ""

    # prefer normalized numeric column if present
    sample_df = None
    if "_bytes_num" in working.columns and working["_bytes_num"].notna().any():
        sample_df = working.sort_values("_bytes_num", ascending=False).head(k)
    elif "Bytes" in working.columns:
        # attempt to coerce Bytes to numeric (strip K/M suffixes). fallback to head
        def _parse_bytes(x):
            try:
                if pd.isna(x): return 0
                if isinstance(x, (int, float)): return float(x)
                s = str(x).strip().replace(",", "")
                if s.endswith(("M","m")):
                    return float(s[:-1]) * 1_000_000
                if s.endswith(("K","k")):
                    return float(s[:-1]) * 1_000
                return float(s)
            except Exception:
                return 0
        try:
            working["_bytes_num_tmp"] = working["Bytes"].apply(_parse_bytes)
            sample_df = working.sort_values("_bytes_num_tmp", ascending=False).head(k)
        except Exception:
            sample_df = working.head(k)
    else:
        sample_df = working.head(k)

    records: List[Dict] = []
    for _, r in sample_df.iterrows():
        rec = {
            "time": str(_val(r, "Date first seen") or _val(r, "Date") or ""),
            "src": _val(r, "Src IP Addr"),
            "dst": _val(r, "Dst IP Addr"),
            "proto": _val(r, "Proto"),
            "bytes": str(_val(r, "Bytes") or _val(r, "_bytes_num") or ""),
            "packets": str(_val(r, "Packets")),
            "attackType": _val(r, "attackType") or "",
            "raw": " | ".join(str(v) for v in r.values)
        }
        records.append(rec)

    return records
