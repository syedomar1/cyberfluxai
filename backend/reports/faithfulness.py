# backend/reports/faithfulness.py
import re
from typing import Dict, List

def compute_simple_faithfulness(llm_output: Dict, evidence_list: List[Dict]) -> Dict:
    """
    Simple heuristic: find IP tokens in LLM output and see if they exist in evidence_list (src or dst).
    Returns {trust, ips_claimed, ips_verified}.
    """
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    text = (llm_output.get("summary", "") or "") + " "
    for rec in llm_output.get("recommendations", []) if isinstance(llm_output.get("recommendations", []), list) else []:
        text += (rec.get("text", "") or "") + " "

    ips = set(re.findall(ip_pattern, text))
    verified = 0
    for ip in ips:
        if any(ip == (e.get("src") or "") or ip == (e.get("dst") or "") for e in evidence_list):
            verified += 1

    trust = (verified / len(ips)) if ips else 1.0
    return {"trust": round(trust, 2), "ips_claimed": list(ips), "ips_verified": int(verified)}
