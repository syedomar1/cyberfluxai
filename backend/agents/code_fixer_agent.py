# backend/agents/code_fixer_agent.py
"""
Simple intelligent fixer for short Python snippets produced by LLMs.
Heuristics:
 - Extract code from triple-backticks / ```python blocks.
 - Replace “smart” unicode quotes/dashes.
 - If LLM returned a single expression (no newlines, no 'result'), wrap with `result = <expr>`.
 - Remove common dangerous keywords (import os, open, subprocess) as a last resort.
 - Try ast.parse() to validate. If parsing fails, return the best-effort fixed code (or original).
Note: This is a best-effort tool for developer convenience, NOT a formal code repair system.
"""

import re
import ast


SMART_REPL = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2014": "-", "\u2013": "-", "\u2026": "...", "\u00a0": " "
}

DANGEROUS_PATTERNS = [
    r'\bimport\s+os\b', r'\bimport\s+sys\b', r'\bopen\s*\(', r'\bsubprocess\b',
    r'\bos\.system\b', r'\beval\s*\(', r'\bexec\s*\('
]


def _replace_smart(s: str) -> str:
    for a, b in SMART_REPL.items():
        s = s.replace(a, b)
    return s


def extract_code_block(text: str) -> str:
    """
    Try to extract the most likely code block from text returned by LLM.
    Prefers triple-backtick blocks, then fenced python blocks, then ```...```.
    If not found returns original text trimmed.
    """
    if not text:
        return ""
    # look for ```python ... ``` or ``` ... ```
    m = re.search(r"```(?:python)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # look for <code> ... </code>
    m = re.search(r"<code>\s*([\s\S]*?)</code>", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # attempt to find a leading "```" or "```py" still; else fallback to whole text
    # also try to extract anything after "```" style markers not closed
    m = re.search(r'(^\s*def\s+|^\s*result\s*=|^\s*import\s+|^\s*df\.)', text, re.MULTILINE)
    if m:
        # assume the whole text is code-like if it contains pythonic hints
        return text.strip()
    return text.strip()


def _looks_like_single_expr(code: str) -> bool:
    # heuristics: no newline or only one line, and starts with "df." or a function call or bracket expression
    lines = [l for l in code.strip().splitlines() if l.strip()]
    if len(lines) == 1:
        l = lines[0].strip()
        # if it starts with 'result =' then not single expr
        if l.startswith("result"):
            return False
        # if begins like df[ or df. or ( or [ or is a call
        if l.startswith("df.") or l.startswith("df[") or l.startswith("(") or l.startswith("[") or re.match(r'^[\w_]+\(', l):
            return True
        # not too long and doesn't contain assignment
        if len(l) < 400 and "=" not in l:
            return True
    return False


def _sanitize_dangerous(code: str) -> str:
    """
    Remove or neutralize obviously dangerous substrings.
    We'll comment them out rather than delete, for debugging.
    """
    for pat in DANGEROUS_PATTERNS:
        code = re.sub(pat, lambda m: "# [REMOVED_DANGEROUS] " + m.group(0), code, flags=re.IGNORECASE)
    return code


def fix_invalid_code(raw_text: str) -> str:
    """
    Primary entry. Returns a "fixed" code string (best-effort).
    If no reliable fix exists returns the original snippet (but cleaned).
    """
    if not raw_text:
        return raw_text or ""

    # 1) extract plausible code
    code = extract_code_block(raw_text)

    # 2) normalize smart quotes, etc.
    code = _replace_smart(code)

    # 3) strip leading prompt/answer tokens like 'Answer:' 'Result:' etc.
    code = re.sub(r'^(Answer:|Result:|Output:)\s*', '', code, flags=re.IGNORECASE)

    # 4) If LLM returned JSON with a 'code' property inside text, try to extract that
    #   quick approach: look for "code": "..." or code":'''...''' patterns
    m_json_code = re.search(r'"code"\s*:\s*"(.*?)"(,|\})', code, re.DOTALL)
    if m_json_code:
        inner = m_json_code.group(1)
        # unescape common escapes
        inner = inner.encode('utf-8').decode('unicode_escape')
        code = inner.strip()

    # 5) If it's a single expression, wrap into result variable
    if _looks_like_single_expr(code) and "result" not in code:
        code = f"result = {code.strip()}"

    # 6) sanitize obviously dangerous substrings
    code = _sanitize_dangerous(code)

    # 7) Try to parse using ast to see if it's valid now
    try:
        ast.parse(code)
        # looks good
        return code
    except SyntaxError as se:
        # Try simple heuristic: if missing parentheses in print (py2->py3) or trailing commas
        # Usually not easy to auto-fix. We'll try minimal fixes:
        # - If code contains unmatched backticks or fenced markers, remove them
        code2 = re.sub(r'`+', '', code)
        code2 = re.sub(r'^\s*<.*?>\s*', '', code2)
        try:
            ast.parse(code2)
            return code2
        except Exception:
            # Last resort: if it's multi-line and contains an expression at the end, wrap last line into result
            lines = code.splitlines()
            if lines:
                last = lines[-1].strip()
                if last and "=" not in last and len(last) < 400:
                    # Wrap last as result
                    attempt = "\n".join(lines[:-1] + [f"result = {last}"])
                    try:
                        ast.parse(attempt)
                        return attempt
                    except Exception:
                        pass
            # cannot parse; return cleaned code (so caller can show both snippet and error)
            return code
    except Exception:
        return code
