# backend/reports/llm_helpers.py
from dotenv import load_dotenv
load_dotenv()

import os
import json
from typing import Dict, List, Any

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

def safe_parse_json(blob: str) -> Dict[str, Any]:
    try:
        return json.loads(blob)
    except Exception:
        import re
        m = re.search(r'({[\s\S]*})', blob)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return {"summary_raw": blob}

def llm_generate_summary(metrics: Dict, evidence: List[Dict], model_hint: str = "gpt-4o-mini") -> Dict:
    """
    Return JSON-like summary with keys 'summary' and 'recommendations' if possible.
    Uses new OpenAI client if available; falls back to older 'openai' usage.
    If no OPENAI_KEY, returns deterministic fallback.
    """
    evidence_text = "\n".join(
        f"[{i}] {e.get('time','')} | {e.get('src','')} -> {e.get('dst','')} | bytes={e.get('bytes','')} | attackType={e.get('attackType','')}"
        for i, e in enumerate(evidence)
    )

    prompt = f"""
You are a concise cyber security analyst. Using ONLY the metrics and evidence below, produce JSON with:
- summary: 2-4 sentence executive summary
- recommendations: list of objects like {{'text': ..., 'evidence_ids': [ints]}}

Return ONLY valid JSON.

METRICS:
{json.dumps(metrics, indent=2)}

EVIDENCE:
{evidence_text}
"""

    if not OPENAI_KEY:
        # deterministic fallback when no key
        summary = f"{metrics.get('total_rows','?')} rows, {metrics.get('unique_attack_types',0)} unique attack types. Top: {list(metrics.get('top_attack_types',{}).keys())[:1]}"
        recs = []
        if evidence:
            recs = [
                {"text": "Investigate top source IP (highest bytes).", "evidence_ids": [0]},
                {"text": "Check large flows for possible exfiltration.", "evidence_ids": [0]},
            ]
        return {"summary": summary, "recommendations": recs}

    # Prefer new OpenAI client interface if available
    try:
        # new client: from openai import OpenAI; client = OpenAI()
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        # choose a model name; user can change as needed
        model_name = model_hint
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role":"user", "content": prompt}],
            temperature=0.0,
            max_tokens=400
        )
        # response shape: resp.choices[0].message.content
        content = ""
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            # new client returns objects with .message.content
            ch = resp.choices[0]
            # many runtimes return .message with .content
            content = getattr(getattr(ch, "message", ch), "content", None) or ch.get("message", {}).get("content", "") or ch.get("text","")
        else:
            content = str(resp)
        parsed = safe_parse_json(content)
        return parsed
    except Exception as e_new:
        # fallback attempt old 'openai' library usage
        try:
            import openai
            openai.api_key = OPENAI_KEY
            # older API
            resp = openai.ChatCompletion.create(
                model="gpt-4o" if "gpt-4o" in [] else "gpt-3.5-turbo",
                messages=[{"role":"user","content":prompt}],
                temperature=0.0,
                max_tokens=400
            )
            text = resp["choices"][0]["message"]["content"]
            parsed = safe_parse_json(text)
            return parsed
        except Exception as e_old:
            # return detailed error for debugging (kept concise in production)
            return {"summary_raw": f"LLM call error:\n{str(e_new)}\n{str(e_old)}"}
