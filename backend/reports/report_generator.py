# backend/reports/report_generator.py
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import unicodedata
import math
import json

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:
    Image = None
    _HAS_PIL = False

from reports.utils import load_logs_csv, compute_basic_metrics, sample_evidence_rows

try:
    from reports.faithfulness import compute_simple_faithfulness
    _HAS_FAITH = True
except Exception:
    compute_simple_faithfulness = None
    _HAS_FAITH = False

try:
    from reports import llm_helpers
    _HAS_LLM = True
except Exception:
    llm_helpers = None
    _HAS_LLM = False

try:
    from agents.data_agent import run_llm_query
    _HAS_AGENT = True
except Exception:
    run_llm_query = None
    _HAS_AGENT = False

sns.set(style="darkgrid")

BASE_DIR = os.path.dirname(__file__)
TMP_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "tmp_reports"))
os.makedirs(TMP_DIR, exist_ok=True)


def safe_str(x: Any) -> str:
    if x is None:
        return ""
    s = str(x)
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00a0": " ",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s)
    try:
        b = s.encode("latin-1", errors="ignore")
        return b.decode("latin-1")
    except Exception:
        return "".join(ch for ch in s if ord(ch) < 128)


def safe_truncate(s: Any, max_len: int = 140, tail: str = "...") -> str:
    if s is None:
        return ""
    st = str(s)
    if len(st) <= max_len:
        return st
    # prefer to cut at a comma or space near the boundary
    cut = max_len
    for sep in [",", " ", ";"]:
        idx = st.rfind(sep, 0, max_len)
        if idx > int(max_len * 0.6):
            cut = idx
            break
    return st[:cut].rstrip() + tail


def pretty_bytes(value: Any) -> str:
    """
    Normalize bytes-like values (numbers or strings like '2.5 M', '64.8 M') into a human-friendly format.
    Returns e.g. '3.2 MB', '512 B', or original string if unparseable.
    """
    if value is None:
        return ""
    # If already a number (int/float), format
    try:
        if isinstance(value, (int, float)) and not pd.isna(value):
            n = float(value)
            # Use 1024 base only when it's an actual byte count; many flows use metric (M => million).
            # We will show as MB (1e6) if >= 1e6, else KB if >=1e3
            if abs(n) >= 1_000_000:
                return f"{n/1_000_000:.2f} M"
            if abs(n) >= 1000:
                return f"{n/1000:.1f} K"
            return f"{int(n)} B"
    except Exception:
        pass

    s = str(value).strip()
    # Convert patterns like '2.3 M' or '64.8 M' etc:
    try:
        s_clean = s.replace(",", "").lower()
        # if it ends with 'm' or 'mb' etc.
        if s_clean.endswith("mb") or s_clean.endswith("m"):
            num = float(s_clean.rstrip("mbm ").strip())
            return f"{num:.2f} M"
        if s_clean.endswith("kb") or s_clean.endswith("k"):
            num = float(s_clean.rstrip("kbk ").strip())
            return f"{num:.1f} K"
        if s_clean.endswith("b"):
            num = float(s_clean.rstrip("b ").strip())
            # if large, convert to M
            if abs(num) >= 1_000_000:
                return f"{num/1_000_000:.2f} M"
            if abs(num) >= 1000:
                return f"{num/1000:.1f} K"
            return f"{int(num)} B"
        # sometimes the string contains multiple segments (LLM concatenation). Return truncated.
        if any(ch.isalpha() for ch in s_clean) and len(s_clean) > 20:
            return safe_truncate(s, 30)
        # try parse as plain number
        num = float(s_clean)
        return pretty_bytes(num)
    except Exception:
        # fallback to truncated original
        return safe_truncate(s, 40)


def _save_plot(fig: plt.Figure, fname: str) -> str:
    path = os.path.join(TMP_DIR, fname)
    try:
        fig.tight_layout()
    except Exception:
        pass
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_attack_counts(attack_counts: pd.Series, figsize=(11, 4.0)) -> Optional[str]:
    if attack_counts is None or attack_counts.empty:
        return None
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(x=attack_counts.values, y=attack_counts.index, ax=ax, palette="mako")
    ax.set_xlabel("Count")
    ax.set_title("Attack Type Frequency")
    return _save_plot(fig, "attack_type_freq.png")


def _plot_top_ips(series: pd.Series, title: str, filename: str, figsize=(11, 4.0)) -> Optional[str]:
    if series is None or series.empty:
        return None
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(x=series.values, y=series.index, ax=ax, palette="viridis")
    ax.set_xlabel("Count")
    ax.set_title(title)
    return _save_plot(fig, filename)


def _plot_flows(bytes_by_flow: pd.Series, figsize=(11, 4.0)) -> Optional[str]:
    if bytes_by_flow is None or bytes_by_flow.empty:
        return None
    values_mb = bytes_by_flow / (1024 * 1024)
    # labels simplified
    labels = [f"{s}->{d}" for s, d in values_mb.index]
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(x=values_mb.values, y=labels, ax=ax, palette="rocket")
    ax.set_xlabel("MB")
    ax.set_title("Top Flows by Bytes (MB)")
    return _save_plot(fig, "top_flows_bytes.png")


def _plot_timeline(timeline_series, figsize=(11, 3.5)) -> Optional[str]:
    if timeline_series is None:
        return None
    try:
        if isinstance(timeline_series, dict):
            s = pd.Series(timeline_series)
            s.index = pd.to_datetime(s.index, errors="coerce")
            s = s.sort_index()
        else:
            s = timeline_series
        if getattr(s, "empty", False):
            return None
        fig, ax = plt.subplots(figsize=figsize)
        s.plot(ax=ax, color="#7e30e1")
        ax.set_title("Event Timeline (hourly counts)")
        ax.set_ylabel("Events / hour")
        return _save_plot(fig, "timeline.png")
    except Exception:
        return None


def summarize_preview(obj: Any, rows: int = 5, max_field_len: int = 80) -> str:
    """
    Convert a result_preview / DataFrame / list into a short string for inclusion in PDF.
    Keeps only first `rows` items / head(). Truncates long values.
    """
    try:
        if isinstance(obj, pd.DataFrame):
            head = obj.head(rows)
            # create a compact string representation
            lines = []
            cols = list(head.columns)
            # header
            lines.append(", ".join(cols))
            for _, r in head.iterrows():
                vals = []
                for c in cols:
                    v = r.get(c, "")
                    vals.append(safe_truncate(v, max_len=max_field_len))
                lines.append(", ".join(vals))
            return "\n".join(lines)
        if isinstance(obj, (list, tuple)):
            lines = []
            for i, item in enumerate(obj[:rows]):
                if isinstance(item, dict):
                    # flatten keys
                    kvs = []
                    for k, v in list(item.items())[:6]:
                        kvs.append(f"{k}={safe_truncate(v, max_len=max_field_len)}")
                    lines.append("{" + ", ".join(kvs) + "}")
                else:
                    lines.append(safe_truncate(item, max_len=max_field_len))
            if len(obj) > rows:
                lines.append(f"... ({len(obj)} items total)")
            return "\n".join(lines)
        if isinstance(obj, dict):
            # show top 8 keys
            lines = []
            for i, (k, v) in enumerate(obj.items()):
                lines.append(f"{k}: {safe_truncate(v, max_len=max_field_len)}")
                if i >= 7:
                    break
            if len(obj) > 8:
                lines.append(f"... ({len(obj)} keys total)")
            return "\n".join(lines)
        # fallback - string
        return safe_truncate(obj, max_len=max_field_len * 2)
    except Exception:
        return safe_truncate(obj, max_len=max_field_len)


def summarize_agent_result(out: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert the raw `out` object from run_llm_query into short printable fields:
    - short_answer: truncated LLM answer text (if any)
    - short_code: truncated code (first & last lines)
    - short_preview: summarized result preview
    - status/error
    """
    status = out.get("status", "unknown")
    short = {"status": status}
    raw = out.get("raw_llm") or out.get("raw", "") or ""
    # short answer
    if out.get("answer"):
        short["short_answer"] = safe_truncate(out.get("answer"), max_len=200)
    elif isinstance(raw, str) and raw:
        short["short_answer"] = safe_truncate(raw, max_len=220)
    else:
        short["short_answer"] = ""

    code = out.get("code") or out.get("executed_code") or ""
    code = safe_truncate(code, max_len=800)
    short["short_code"] = code

    preview = out.get("result_preview") or out.get("result") or out.get("sample") or out.get("result_preview")
    if preview is not None:
        short["short_preview"] = summarize_preview(preview, rows=6, max_field_len=80)
    else:
        short["short_preview"] = ""

    if status != "success":
        err = out.get("error") or out.get("exec_error") or out.get("trace") or out.get("traceback") or ""
        short["error"] = safe_truncate(err, max_len=500)
    else:
        short["error"] = ""
    return short


def _format_two_column_summary(pdf: FPDF, left: Dict[str, Any], right: Dict[str, Any]):
    # This prints each pair in one "row", but left & right use multi_cell to avoid clipping and concatenation.
    width = pdf.w - 24
    col_w = width / 2 - 6
    pdf.set_font("Arial", size=10)
    left_items = list(left.items())
    right_items = list(right.items())
    rows = max(len(left_items), len(right_items))
    start_x = pdf.get_x()
    for i in range(rows):
        left_text = ""
        right_text = ""
        if i < len(left_items):
            k, v = left_items[i]
            left_text = f"{k}: {v}"
        if i < len(right_items):
            rk, rv = right_items[i]
            right_text = f"{rk}: {rv}"
        # left column
        x_before = pdf.get_x()
        y_before = pdf.get_y()
        pdf.multi_cell(col_w, 6, safe_str(left_text), border=0)
        # set position for right column on same line
        pdf.set_xy(x_before + col_w + 6, y_before)
        pdf.multi_cell(col_w, 6, safe_str(right_text), border=0)
        # move cursor to next row start
        pdf.set_xy(start_x, max(y_before + 6, pdf.get_y()))


def generate_logs_report(
    csv_filename: str = "logs.csv",
    output_filename: Optional[str] = None,
    nrows: Optional[int] = None,
    include_ai: bool = False,
    layout: str = "single"   # default "single" = continuous & readable
) -> Dict[str, Any]:
    df = load_logs_csv(csv_filename, nrows=nrows)
    df.columns = [str(c).strip() for c in df.columns]

    def _parse_bytes_val(x):
        try:
            if pd.isna(x): return 0.0
            if isinstance(x, (int, float)): return float(x)
            st = str(x).strip().replace(",", "")
            # handle human suffix M/K used in some datasets
            if st.endswith(("M","m")):
                return float(st[:-1]) * 1_000_000
            if st.endswith(("K","k")):
                return float(st[:-1]) * 1_000
            # also allow values with spaces like '2.5 M 10.3 M' - not parseable to single float
            if " " in st and any(ch.isalpha() for ch in st):
                # not a single value: return 0 and let previews show summarized string
                return 0.0
            return float(st)
        except Exception:
            return 0.0

    # compute numeric bytes column for aggregations while preserving original 'Bytes' for previews
    df["_bytes_num"] = df["Bytes"].apply(_parse_bytes_val) if "Bytes" in df.columns else 0.0

    metrics = compute_basic_metrics(df)
    total_records = metrics.get("total_rows", len(df))
    suspicious = metrics.get("suspicious_rows", 0)

    attack_counts = df["attackType"].fillna("unknown").value_counts().head(20) if "attackType" in df.columns else pd.Series(dtype=int)
    top_src = df["Src IP Addr"].value_counts().head(10) if "Src IP Addr" in df.columns else pd.Series(dtype=int)
    top_dst = df["Dst IP Addr"].value_counts().head(10) if "Dst IP Addr" in df.columns else pd.Series(dtype=int)
    bytes_by_flow = (df.groupby(["Src IP Addr", "Dst IP Addr"])["_bytes_num"].sum().sort_values(ascending=False).head(12)) if "_bytes_num" in df.columns else pd.Series(dtype=float)

    timeline = None
    for cand in ["Date first seen", "Date", "timestamp", "time", "datetime"]:
        if cand in df.columns:
            try:
                s = pd.to_datetime(df[cand], errors="coerce")
                timeline = s.dropna().dt.floor("H").value_counts().sort_index()
            except Exception:
                timeline = None
            break

    # Choose fig sizes based on layout
    if layout == "single":
        attack_figsize = (11, 4.0)
        ips_figsize = (11, 4.0)
        flows_figsize = (11, 4.0)
        timeline_figsize = (11, 3.5)
    else:
        attack_figsize = (8.5, 3.2)
        ips_figsize = (8.5, 3.2)
        flows_figsize = (8.5, 3.2)
        timeline_figsize = (9.0, 2.8)

    fig_paths: List[str] = []
    p = _plot_attack_counts(attack_counts, figsize=attack_figsize)
    if p: fig_paths.append(os.path.basename(p))
    p = _plot_top_ips(top_src, "Top Source IPs", "top_src_ips.png", figsize=ips_figsize)
    if p: fig_paths.append(os.path.basename(p))
    p = _plot_top_ips(top_dst, "Top Destination IPs", "top_dst_ips.png", figsize=ips_figsize)
    if p: fig_paths.append(os.path.basename(p))
    p = _plot_flows(bytes_by_flow, figsize=flows_figsize)
    if p: fig_paths.append(os.path.basename(p))
    p = _plot_timeline(timeline, figsize=timeline_figsize)
    if p: fig_paths.append(os.path.basename(p))

    # LLM / agent
    llm_output = {}
    agent_results = []
    if include_ai:
        try:
            evidence = sample_evidence_rows(df, k=8)
            if _HAS_LLM and hasattr(llm_helpers, "llm_generate_summary"):
                llm_output = llm_helpers.llm_generate_summary(metrics, evidence) or {}
            else:
                top_attack_list = list(metrics.get("top_attack_types",{}).keys())[:3]
                llm_output = {"summary": f"{total_records} rows, {metrics.get('unique_attack_types',0)} unique attack types. Top: {top_attack_list}", "recommendations":[{"text":"Inspect top source IPs for suspicious behavior","evidence_ids":[0]}]}
        except Exception as e:
            llm_output = {"summary_raw": f"LLM call error: {str(e)}"}

        if _HAS_AGENT and run_llm_query:
            diag_questions = [
                "Group by 'Src IP Addr' and compute total bytes and flow counts; return a DataFrame with columns 'src','total_bytes','flows' sorted descending by total_bytes assigned to variable result.",
                "If 'attackType' exists, return counts per attackType and a small sample for the top attackType (assign to result)."
            ]
            for q in diag_questions:
                try:
                    out = run_llm_query(df, q)
                    # summarize the agent output promptly to avoid huge payloads
                    short = summarize_agent_result(out)
                    agent_results.append({"question": q, "raw": out, "summary": short})
                except Exception as e:
                    agent_results.append({"question": q, "raw": {"status":"error","error":str(e)}, "summary": {"status":"error","error": safe_truncate(str(e), 300)}})

    # detection metrics
    det_metrics = {}
    try:
        if "attackType" in df.columns and "detector_label" in df.columns:
            from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
            y_true = (df['attackType'].astype(str).str.lower() != 'normal').astype(int)
            y_pred = (df['detector_label'].astype(str).str.lower() != 'normal').astype(int)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            cm = confusion_matrix(y_true, y_pred).tolist()
            det_metrics = {"precision": round(float(precision),3), "recall": round(float(recall),3), "f1": round(float(f1),3), "confusion_matrix": cm}
    except Exception:
        det_metrics = {}

    if output_filename is None:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        output_filename = os.path.join(TMP_DIR, f"cyberflux_report_{ts}.pdf")
    else:
        output_filename = os.path.abspath(output_filename)

    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)

    # Cover
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, safe_str("CyberFluxAI — Incident Summary"), ln=1, align="C")
    pdf.ln(4)
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, safe_str(f"Source: {os.path.basename(csv_filename)}"), ln=1, align="C")
    pdf.cell(0, 6, safe_str(f"Generated: {datetime.utcnow().isoformat()} UTC"), ln=1, align="C")
    pdf.ln(8)

    # Exec summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, safe_str("Executive Summary"), ln=1)
    pdf.set_font("Arial", size=10)
    # Format numbers nicely and keep top samples short
    left = {"Total records": f"{int(total_records):,}", "Suspicious records": f"{int(suspicious):,}", "Unique attack types": metrics.get("unique_attack_types",0)}
    # metrics.get("top_src_ips") might be a dict or series; present top 3
    def top_sample(d):
        if not d: return []
        if isinstance(d, (dict, pd.Series)):
            items = list(d.items()) if isinstance(d, dict) else list(d.items())
            return [(k, int(v)) for k, v in items][:3]
        return []
    right = {"Top src (sample)": top_sample(metrics.get("top_src_ips", {})), "Top dst (sample)": top_sample(metrics.get("top_dst_ips", {}))}
    _format_two_column_summary(pdf, left, right)
    pdf.ln(6)

    # LLM summary
    if include_ai and llm_output:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, safe_str("Executive Summary (LLM)"), ln=1)
        pdf.set_font("Arial", size=10)
        if isinstance(llm_output, dict) and "summary" in llm_output:
            pdf.multi_cell(0, 6, safe_str(llm_output.get("summary","")))
        else:
            pdf.multi_cell(0, 6, safe_str(llm_output.get("summary_raw","(no LLM summary)")))
        pdf.ln(4)
        recs = llm_output.get("recommendations", [])
        if isinstance(recs, list) and recs:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 6, safe_str("Recommendations (LLM)"), ln=1)
            pdf.set_font("Arial", size=10)
            for r in recs:
                pdf.multi_cell(0, 6, safe_str(f"- {r.get('text','')} (evidence: {r.get('evidence_ids',[])})"))
            pdf.ln(4)

    # Embed figures inline (one after another) - keeps them continuous
    for fig_basename in fig_paths:
        fig_file = os.path.join(TMP_DIR, fig_basename)
        if not os.path.isfile(fig_file):
            continue
        # Title and inline figure (not forcing new page)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, safe_str(os.path.splitext(fig_basename)[0].replace("_"," ").title()), ln=1)
        max_w = pdf.w - 24
        try:
            pdf.image(fig_file, w=max_w)
        except Exception:
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, safe_str("[Figure could not be embedded]"))
        pdf.ln(6)

    # Agentic queries output (if any) - show summarized output only
    if agent_results:
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, safe_str("Agentic Queries (LLM-generated)"), ln=1)
        pdf.set_font("Arial", size=10)
        for a in agent_results:
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(0, 6, safe_str("Q: " + a.get("question","")))
            pdf.set_font("Arial", size=10)
            summ = a.get("summary", {})
            # status line
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 5, safe_str(f"Status: {summ.get('status','unknown')}"), ln=1)
            pdf.set_font("Arial", size=10)
            if summ.get("short_answer"):
                pdf.multi_cell(0, 5, safe_str("LLM answer: " + summ.get("short_answer","")))
            if summ.get("short_code"):
                pdf.set_font("Courier", size=9)
                pdf.multi_cell(0, 5, safe_str("Code (truncated):\n" + summ.get("short_code","")))
                pdf.set_font("Arial", size=10)
            if summ.get("short_preview"):
                pdf.set_font("Courier", size=9)
                pdf.multi_cell(0, 5, safe_str("Result preview:\n" + summ.get("short_preview","")))
                pdf.set_font("Arial", size=10)
            if summ.get("error"):
                pdf.set_text_color(180, 30, 30)
                pdf.multi_cell(0, 5, safe_str("Agent error: " + summ.get("error","(no detail)")))
                pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

    # Detector metrics page
    if det_metrics:
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, safe_str("Detector Performance"), ln=1)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, safe_str(f"Precision: {det_metrics.get('precision')}  Recall: {det_metrics.get('recall')}  F1: {det_metrics.get('f1')}"), ln=1)
        cm = det_metrics.get("confusion_matrix")
        if cm:
            pdf.ln(2)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 6, safe_str("Confusion Matrix (rows=true, cols=pred):"), ln=1)
            pdf.set_font("Arial", size=10)
            for row in cm:
                pdf.multi_cell(0, 6, safe_str(" | ".join(str(int(x)) for x in row)))
        pdf.ln(4)

    # Evidence
    evidence = sample_evidence_rows(df, k=8)
    if evidence:
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, safe_str("Sample Evidence (top rows)"), ln=1)
        pdf.set_font("Courier", size=9)
        for i, r in enumerate(evidence):
            header = f"[{i}] {r.get('time','')} | {r.get('src','')} -> {r.get('dst','')} | bytes={pretty_bytes(r.get('bytes',''))} | attackType={r.get('attackType','')}"
            pdf.multi_cell(0, 5, safe_str(header))
            raw = r.get("raw","")
            raw = safe_truncate(raw, max_len=140)
            pdf.set_text_color(110,110,110)
            pdf.multi_cell(0,5, safe_str(" raw: " + raw))
            pdf.set_text_color(0,0,0)
            pdf.ln(1)

    # Top attack types table
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, safe_str("Top Attack Types"), ln=1)
    pdf.set_font("Arial", size=10)
    if not attack_counts.empty:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(120, 7, safe_str("Attack Type"), border=1)
        pdf.cell(40, 7, safe_str("Count"), border=1, ln=1)
        pdf.set_font("Arial", size=10)
        for k, v in attack_counts.head(12).items():
            pdf.cell(120, 6, safe_str(str(k)), border=1)
            pdf.cell(40, 6, safe_str(str(int(v))), border=1, ln=1)
    else:
        pdf.multi_cell(0, 6, safe_str("No attackType column found or empty."))

    pdf.output(output_filename)

    meta = {
        "pdf_path": os.path.abspath(output_filename),
        "num_records": int(total_records),
        "suspicious_records": int(suspicious),
        "figures": fig_paths,
        "llm_output": llm_output,
        "agent_results": agent_results,
        "detector_metrics": det_metrics
    }
    return meta
