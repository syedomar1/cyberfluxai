# backend/agents/data_agent.py
from dotenv import load_dotenv
load_dotenv()

import ast
import json
import os
import traceback
from typing import Dict, Any
import pandas as pd

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

# Import fixer from the other module
try:
    from agents.code_fixer_agent import fix_invalid_code, extract_code_block
except Exception:
    # fallback: stub (should not happen if code present)
    def fix_invalid_code(x): return x
    def extract_code_block(x): return x

def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False

def extract_json_from_text(text: str) -> Dict:
    import re
    m = re.search(r'({[\s\S]*})', text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return {}

def _get_text_from_openai_response(resp) -> str:
    """
    Normalize response object from new/old SDK to text string.
    """
    try:
        # new client object: resp.choices[0].message.content or similar
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            ch = resp.choices[0]
            # try message.content then text
            if hasattr(ch, "message") and getattr(ch.message, "content", None):
                return ch.message.content
            if isinstance(ch, dict):
                return ch.get("message", {}).get("content") or ch.get("text") or str(ch)
            return str(ch)
        # fallback: resp as string
        return str(resp)
    except Exception:
        return str(resp)

def run_llm_query(df: pd.DataFrame, question: str, model: str="gpt-4o-mini") -> Dict[str, Any]:
    """
    Ask LLM to produce Python code that sets `result`.
    Returns dict with status, error details or preview.
    """
    cols = ", ".join([f"'{c}'" for c in df.columns.tolist()])
    prompt = f"""
You are a strict Python/pandas analyst. The DataFrame variable is `df` and has columns: {cols}.

You must produce either:
1) A JSON object with keys 'answer' and 'code' where 'code' is Python that assigns the final output to `result`, OR
2) Plain Python code that assigns the analysis output to a variable named `result`.

Constraints:
- Only use pandas/numpy operations (pd, np available).
- No file IO, no shell, no imports.
- The snippet MUST assign `result`.
- Keep it short and deterministic.

Question:
{question}

Return only code or a JSON wrapper (no extra commentary).
"""

    if not OPENAI_KEY:
        return {"status":"error", "error":"OpenAI key not configured on server."}

    raw_text = None
    # Try new OpenAI client first
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":prompt}],
            temperature=0.0,
            max_tokens=700
        )
        raw_text = _get_text_from_openai_response(resp)
    except Exception as e_new:
        # fallback: older openai usage
        try:
            import openai
            openai.api_key = OPENAI_KEY
            resp = openai.ChatCompletion.create(model=model, messages=[{"role":"user","content":prompt}], temperature=0.0, max_tokens=700)
            raw_text = resp["choices"][0]["message"]["content"]
        except Exception as e_old:
            return {"status":"error", "error": f"LLM call failed. NewErr:{str(e_new)} OldErr:{str(e_old)}"}

    # 1) attempt to extract JSON with 'code'
    parsed_json = extract_json_from_text(raw_text)
    code = ""
    answer_text = ""
    if parsed_json and "code" in parsed_json:
        code = parsed_json["code"]
        answer_text = parsed_json.get("answer", "")
    else:
        # try to extract code block
        code = extract_code_block(raw_text)
        # if that fails, use raw_text (last resort)
        if not code:
            code = raw_text or ""

        # try to pick an 'answer' if JSON existed
        if parsed_json and "answer" in parsed_json:
            answer_text = parsed_json["answer"]

    # ensure code contains 'result' assignment; if LLM returned an expression, fix it
    if "result" not in code:
        # use solver from fixer: this may wrap expressions
        maybe_fixed = fix_invalid_code(code)
        if "result" not in maybe_fixed and is_valid_python(maybe_fixed):
            # if valid but no result, try heuristics: if single expr, wrap
            lines = [l for l in maybe_fixed.splitlines() if l.strip()]
            if len(lines) == 1 and "=" not in maybe_fixed:
                maybe_fixed = f"result = {maybe_fixed.strip()}"
        code = maybe_fixed

    # Validate syntax
    if not is_valid_python(code):
        # try fixer again more aggressively
        code2 = fix_invalid_code(code)
        if is_valid_python(code2):
            code = code2
        else:
            # still invalid — return helpful diagnostics
            return {
                "status":"error",
                "error": "LLM returned invalid/unparsable Python and fixer couldn't fix it.",
                "raw_llm": raw_text,
                "attempted_fix": code2,
                "trace": None
            }

    # Basic security: forbid certain builtins if present (sanitizer already comments out)
    # Execute code in restricted env
    safe_globals = {
        "pd": pd,
        "np": __import__("numpy"),
        "df": df.copy(),
        "__builtins__": {
            'len': len, 'sum': sum, 'min': min, 'max': max, 'sorted': sorted, 'round': round, 'abs': abs,
            'range': range, 'enumerate': enumerate, 'zip': zip, 'list': list, 'dict': dict
        }
    }
    local_vars = {}

    try:
        exec(code, safe_globals, local_vars)
    except Exception as ex:
        tb = traceback.format_exc()
        return {
            "status": "error",
            "error": "Exception during code execution",
            "exec_error": str(ex),
            "traceback": tb,
            "raw_llm": raw_text,
            "executed_code": code
        }

    if "result" not in local_vars:
        # code ran but didn't assign result
        return {
            "status": "error",
            "error": "Code executed but did not set 'result' variable.",
            "executed_code": code,
            "raw_llm": raw_text
        }

    result = local_vars["result"]

    # Convert result into preview-friendly form
    try:
        if isinstance(result, pd.DataFrame):
            preview = result.head(10).to_dict(orient="records")
            rtype = "dataframe"
        elif isinstance(result, (list, tuple)):
            preview = list(result)[:50]
            rtype = type(result).__name__
        elif hasattr(result, "tolist"):
            preview = result.tolist()
            rtype = type(result).__name__
        else:
            preview = result
            rtype = type(result).__name__
    except Exception as e_preview:
        preview = str(result)
        rtype = type(result).__name__

    return {
        "status": "success",
        "answer": answer_text,
        "code": code,
        "result_preview": preview,
        "result_type": rtype,
        "raw_llm": raw_text
    }
