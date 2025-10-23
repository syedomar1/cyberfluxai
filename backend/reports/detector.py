"""Detector training and explainability helpers.

Functions:
 - train_detector(df, target_col='label', features=None, model_type='xgb', out_path=None)
 - explain_top_predictions(model, X, top_k=20)
"""
from typing import Optional, List, Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve, average_precision_score
import joblib

try:
    import xgboost as xgb
except Exception:
    xgb = None

try:
    import shap
except Exception:
    shap = None


def _get_features(df: pd.DataFrame, features: Optional[List[str]] = None) -> Tuple[pd.DataFrame, List[str]]:
    if features:
        return df[features].fillna(0), features
    # heuristics: common columns
    cand = [c for c in df.columns if c.lower() in ("bytes_int", "duration_sec", "src_port", "dst_port") or c.lower().startswith("flag")]
    if not cand:
        cand = [c for c in df.columns if df[c].dtype in ("int64", "float64")][:10]
    return df[cand].fillna(0), cand


def train_detector(df: pd.DataFrame, target_col: str = "label", features: Optional[List[str]] = None, model_type: str = "xgb", out_path: Optional[str] = None) -> Dict:
    X, feat_names = _get_features(df, features)
    y = df[target_col]

    if model_type == "rf":
        base_model = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42)
    else:
        if xgb is None:
            raise RuntimeError("xgboost is required for model_type='xgb'")
        base_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=200, random_state=42)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    probs = cross_val_predict(base_model, X, y, cv=cv, method="predict_proba", n_jobs=-1)
    # choose positive class probability
    pos_probs = probs[:, 1]
    ap = average_precision_score(y, pos_probs)

    # fit final model on full data
    base_model.fit(X, y)

    model_meta = {"model_type": model_type, "features": feat_names, "average_precision": float(ap)}
    if out_path:
        joblib.dump({"model": base_model, "meta": model_meta}, out_path)

    return {"model": base_model, "meta": model_meta, "probs": pos_probs}


def explain_top_predictions(model: Any, X: pd.DataFrame, top_k: int = 20) -> Dict:
    """Compute SHAP explanations for top_k highest-probability suspicious records.

    Returns: {shap_values: array, expected_value, top_indices}
    """
    if shap is None:
        raise RuntimeError("shap is required to compute explanations")
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
    else:
        probs = model.predict(X)
    idx = np.argsort(-probs)[:top_k]

    # use TreeExplainer for tree models, else KernelExplainer
    try:
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X.iloc[idx])
    except Exception:
        # fallback to KernelExplainer (slow)
        explainer = shap.KernelExplainer(model.predict_proba, X.iloc[:100])
        shap_values = explainer.shap_values(X.iloc[idx])

    return {"shap_values": shap_values, "top_indices": idx}
