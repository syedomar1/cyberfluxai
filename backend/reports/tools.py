"""Structured tools for agent use.

Each tool has a small interface and returns JSON-serializable outputs. Agents should only call these tools.
"""
from typing import Any, Dict, List, Optional

import pandas as pd


def pandas_tool(df: pd.DataFrame, query: str, max_rows: int = 50) -> Dict:
    """Run a safe pandas query on DataFrame and return rows as list of dicts.

    query: a pandas.query() expression (no arbitrary code execution). Use this to filter rows.
    """
    try:
        res = df.query(query)
        return {"n_rows": int(len(res)), "rows": res.head(max_rows).to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e)}


def plot_tool(df: pd.DataFrame, x: str, y: str, kind: str = "line", out_path: Optional[str] = None) -> Dict:
    """Create a small matplotlib/plotly plot and save to out_path (if provided) and return summary.
    Returns {n_points, out_path} or error.
    """
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        if kind == "line":
            ax.plot(df[x], df[y], marker='.')
        elif kind == "hist":
            ax.hist(df[y].dropna())
        else:
            ax.scatter(df[x], df[y], s=5)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        if out_path:
            fig.savefig(out_path, bbox_inches='tight')
            return {"n_points": int(len(df)), "out_path": out_path}
        return {"n_points": int(len(df))}
    except Exception as e:
        return {"error": str(e)}


def query_db_tool(db_conn_str: str, sql: str, max_rows: int = 100) -> Dict:
    """Query a SQL database using sqlite3 connection string for safety. Returns rows.
    Only supports sqlite file paths like 'sqlite:///path/to/db.sqlite'.
    """
    try:
        if not db_conn_str.startswith("sqlite:///"):
            return {"error": "Only sqlite:/// connections supported for safety"}
        import sqlite3
        path = db_conn_str.replace("sqlite:///", "")
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
        conn.close()
        return {"columns": cols, "rows": [dict(zip(cols, r)) for r in rows]}
    except Exception as e:
        return {"error": str(e)}
