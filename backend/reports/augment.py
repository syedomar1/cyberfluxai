"""Data augmentation using CTGAN (SDV).

Provides a helper to fit a CTGAN and sample synthetic rows to balance classes.
"""
from __future__ import annotations
from typing import Optional

try:
    from ctgan import CTGANSynthesizer
    import pandas as pd
    import numpy as np
except Exception:
    CTGANSynthesizer = None
    pd = None
    np = None


def train_ctgan_and_augment(df, target_col: str = "label", desired_ratio: float = 1.0, epochs: int = 300) -> Optional["pd.DataFrame"]:
    """Train CTGAN on minority class and generate synthetic samples to reach desired_ratio.

    desired_ratio: desired number of minority / majority (e.g., 1.0 for balanced)
    """
    if CTGANSynthesizer is None or pd is None:
        raise RuntimeError("ctgan and pandas are required for augmentation")
    counts = df[target_col].value_counts()
    if len(counts) < 2:
        return df
    majority = counts.idxmax()
    minority = counts.idxmin()
    n_major = counts.max()
    n_min = counts.min()
    target_n_min = int(n_major * desired_ratio)
    to_generate = max(0, target_n_min - n_min)
    if to_generate == 0:
        return df

    synth = CTGANSynthesizer(epochs=epochs)
    # train on minority rows only to preserve minority distribution
    synth.fit(df[df[target_col] == minority])
    samples = synth.sample(to_generate)

    out = pd.concat([df, samples], ignore_index=True)
    return out
