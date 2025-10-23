"""backend/reports/faithfulness.py

Enhanced faithfulness checks.

Exports:
 - compute_simple_faithfulness(llm_output, evidence)  # backward-compatible
 - compute_detailed_faithfulness(llm_output, evidence_df)

The functions accept either a list of evidence dicts or a pandas.DataFrame.
They cross-check LLM claims (IPs, numeric aggregates, percentages) against aggregates
computed from the evidence and return a structured report with unsupported claims flagged.
"""
import re
from typing import Dict, List, Tuple, Any

try:
    import pandas as pd
except Exception:
    pd = None


IP_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
NUMBER_PATTERN = r"(?P<number>\b\d+[,.]?\d*\b)"
PERCENT_PATTERN = r"(?P<percent>\b\d{1,3}(?:\.\d+)?%\b)"


def _to_dataframe(evidence: Any):
    """Convert evidence (list[dict] or DataFrame) to DataFrame or return None if pandas missing."""
    if pd is None:
        return None
    if isinstance(evidence, pd.DataFrame):
        return evidence
    try:
        return pd.DataFrame(evidence)
    except Exception:
        return None


def compute_simple_faithfulness(llm_output: Dict, evidence_list: List[Dict]) -> Dict:
    """Backward-compatible simple IP check.

    Returns: {trust, ips_claimed, ips_verified}
    """
    text = (llm_output.get("summary", "") or "") + " "
    for rec in llm_output.get("recommendations", []) if isinstance(llm_output.get("recommendations", []), list) else []:
        text += (rec.get("text", "") or "") + " "

    ips = set(re.findall(IP_PATTERN, text))
    verified = 0
    for ip in ips:
        if any(ip == (e.get("src") or "") or ip == (e.get("dst") or "") for e in evidence_list):
            verified += 1

    trust = (verified / len(ips)) if ips else 1.0
    return {"trust": round(trust, 2), "ips_claimed": list(ips), "ips_verified": int(verified)}


def _compute_aggregates(df):
    """Compute useful aggregates from flows DataFrame.

    Returns a dict with counts, top src/dst, total bytes, mean duration, flags distribution.
    """
    if df is None:
        return {}
    aggs = {}
    try:
        aggs["n_rows"] = int(len(df))
        if "src" in df.columns:
            aggs["top_src"] = df["src"].value_counts().head(5).to_dict()
        if "dst" in df.columns:
            aggs["top_dst"] = df["dst"].value_counts().head(5).to_dict()
        for col in ("Bytes_int", "bytes", "bytes_in", "bytes_out"):
            if col in df.columns:
                aggs["total_bytes"] = int(df[col].sum())
                break
        for col in ("Duration_sec", "duration", "time"):
            if col in df.columns:
                aggs["mean_duration"] = float(df[col].mean())
                break
        # flags-like columns: compute distribution for any column containing 'flag' or 'flags'
        flag_cols = [c for c in df.columns if "flag" in c.lower()]
        for c in flag_cols:
            aggs[f"flags_{c}"] = df[c].value_counts().to_dict()
    except Exception:
        pass
    return aggs


def compute_detailed_faithfulness(llm_output: Dict, evidence: Any, tolerance: float = 0.1) -> Dict:
    """Cross-check LLM numeric claims against aggregates from evidence.

    - evidence may be list[dict] or pandas.DataFrame.
    - tolerance is relative tolerance for numeric comparisons (10% default).

    Returns a report dict with:
      - ip_check: same shape as compute_simple_faithfulness
      - aggregates: computed aggregates
      - claims: parsed numeric/percent claims and whether they are supported
      - unsupported_claims: list
    """
    df = _to_dataframe(evidence)
    aggs = _compute_aggregates(df)
    # more useful aggregates for claim checking
    try:
        if df is not None and "attackType" in df.columns:
            attack_counts = df["attackType"].fillna("unknown").value_counts()
            aggs["attack_counts"] = attack_counts.to_dict()
            # suspicious rows (non-normal)
            try:
                aggs["suspicious_rows"] = int((df["attackType"].astype(str).str.lower() != "normal").sum())
            except Exception:
                aggs["suspicious_rows"] = None
        else:
            aggs["attack_counts"] = {}
            aggs["suspicious_rows"] = None
    except Exception:
        aggs.setdefault("attack_counts", {})
        aggs.setdefault("suspicious_rows", None)

    # flatten text to search for claims
    text = (llm_output.get("summary", "") or "") + " "
    for rec in llm_output.get("recommendations", []) if isinstance(llm_output.get("recommendations", []), list) else []:
        text += (rec.get("text", "") or "") + " "

    # IP check
    ip_result = compute_simple_faithfulness(llm_output, evidence if not isinstance(evidence, dict) else [])

    # parse numeric claims, fractions and percentages
    claims = []
    # percentages
    for m in re.finditer(PERCENT_PATTERN, text):
        p = m.group("percent")
        try:
            val = float(p.strip("%"))
            claims.append({"type": "percent", "text": p, "value": val})
        except Exception:
            continue

    # fractions like 'X out of Y' or 'X of Y'
    frac_pattern = re.compile(r"(?P<num>\d{1,3}(?:[\d,]*\d)?)\s*(?:out of|of)\s*(?P<den>\d{1,3}(?:[\d,]*\d)?)", re.IGNORECASE)
    for m in re.finditer(frac_pattern, text):
        try:
            n = float(m.group("num").replace(",", ""))
            d = float(m.group("den").replace(",", ""))
            claims.append({"type": "fraction", "text": m.group(0), "num": n, "den": d, "value": n / max(1.0, d)})
        except Exception:
            continue

    # plain numbers
    for m in re.finditer(NUMBER_PATTERN, text):
        num = m.group("number")
        # skip if looks like IP octet sequence (heuristic)
        if re.match(r"^\d{1,3}$", num) and (num + ".") in text:
            continue
        try:
            v = float(num.replace(",", ""))
            claims.append({"type": "number", "text": num, "value": v})
        except Exception:
            continue

    unsupported = []
    supported = []
    for c in claims:
        ok = False
        # fraction: compare ratio to actual if it references rows/flows
        if c["type"] == "fraction":
            if "row" in text.lower() or "flow" in text.lower() or "record" in text.lower():
                n_actual = aggs.get("n_rows")
                if n_actual:
                    rel = abs((c["num"] / max(1.0, c["den"])) - (c["num"] / max(1.0, c["den"])))
                    # redundant but keep as supported when denominator matches total rows
                    if abs(c["den"] - n_actual) <= max(1, n_actual * tolerance):
                        ok = True
        # percent: check context for suspicious/bytes mentions
        elif c["type"] == "percent":
            ctx = text.lower()
            if "suspicious" in ctx and aggs.get("suspicious_rows") is not None and aggs.get("n_rows"):
                actual_pct = 100.0 * aggs.get("suspicious_rows") / max(1, aggs.get("n_rows"))
                if abs(actual_pct - c["value"]) <= max(1.0, actual_pct * tolerance):
                    ok = True
            elif "bytes" in ctx and "total_bytes" in aggs:
                # skip robust bytes-percent matching for now but mark unknown
                ok = True
        # plain numbers: check rows/flows, or attackType counts
        elif c["type"] == "number":
            ctx = text.lower()
            # check row-like claims
            if any(k in ctx for k in ("row", "flow", "record")):
                n = aggs.get("n_rows")
                if n is not None:
                    rel = abs(c["value"] - n) / max(1.0, n)
                    if rel <= tolerance:
                        ok = True
            # check suspicious count
            if not ok and any(k in ctx for k in ("suspicious", "flagged")) and aggs.get("suspicious_rows") is not None:
                n = aggs.get("suspicious_rows")
                if n is not None:
                    rel = abs(c["value"] - n) / max(1.0, n)
                    if rel <= tolerance:
                        ok = True
            # check attack type counts: look for nearby words matching attack names
            if not ok and aggs.get("attack_counts"):
                # try to see if the number matches any attack type count
                for atk, cnt in aggs["attack_counts"].items():
                    if abs(c["value"] - cnt) <= max(1.0, cnt * tolerance):
                        # only mark ok if attack name is present in text
                        if atk.lower() in text.lower() or atk.replace("_"," ").lower() in text.lower() or atk.split("_")[0].lower() in text.lower():
                            ok = True
                            break
        if ok:
            supported.append(c)
        else:
            unsupported.append(c)

    report = {
        "ip_check": ip_result,
        "aggregates": aggs,
        "claims_parsed": claims,
        "supported_claims": supported,
        "unsupported_claims": unsupported,
    }
    # compute a conservative trust score: start from ip trust and penalize unsupported numeric claims
    trust = float(ip_result.get("trust", 1.0))
    if claims:
        penalty = len(unsupported) / len(claims)
        trust = max(0.0, trust - penalty * 0.5)
    report["trust_score"] = round(trust, 2)
    return report

