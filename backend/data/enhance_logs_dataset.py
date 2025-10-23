#!/usr/bin/env python3
"""
prepare_dataset.py

Generates:
 - logs_clean_minimal.csv  -> original columns + attackType, attackID, attackDescription (safe for older report generation)
 - logs_clean_full.csv     -> full df with helper cols (Bytes_int, Duration_sec, initial_label, cluster, etc.)
 - logs_balanced.csv       -> optional balanced dataset for model training (undersample/oversample/synthesize)

Usage (examples):
 python prepare_dataset.py --input logs.csv
 python prepare_dataset.py --input logs.csv --balance-method oversample --target-per-class 20000
 python prepare_dataset.py --input logs.csv --balance-method synthesize --target-size 172838
"""

import argparse
import csv
import math
import random
import re
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split

# Try optional CTGAN
USE_CTGAN = False
try:
    from ctgan import CTGAN
    USE_CTGAN = True
    print("[i] CTGAN available -> synthesize option can use CTGAN.")
except Exception:
    print("[i] CTGAN not available -> synthesize option will fallback to conservative generation.")

RND = 42
random.seed(RND)
np.random.seed(RND)

# --- utility: autodetect delimiter and load with pandas c-engine to allow low_memory ---
def load_csv_autodetect(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        sample = fh.read(8192)
        try:
            dialect = csv.Sniffer().sniff(sample)
            sep = dialect.delimiter
        except Exception:
            sep = ','
    df = pd.read_csv(path, sep=sep, engine='c', encoding='utf-8', low_memory=False)
    return df

# --- parsing helpers ---
_re_bytes = re.compile(r'^\s*([0-9]*\.?[0-9]+)\s*([KkMmGgTt])?\s*$')

def parse_bytes_cell(x):
    if pd.isnull(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return int(x)
    s = str(x).strip().replace(',', '')
    m = _re_bytes.match(s)
    if m:
        val = float(m.group(1))
        suf = m.group(2)
        if suf:
            suf = suf.upper()
            mul = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}[suf]
            return int(val * mul)
        return int(val)
    try:
        return int(float(s))
    except:
        return np.nan

def parse_packets_cell(x):
    if pd.isnull(x):
        return np.nan
    try:
        s = str(x).strip().replace(',', '')
        return int(float(s))
    except:
        return np.nan

def parse_duration_cell(x):
    if pd.isnull(x):
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    # possible "MM:SS.S" or "HH:MM:SS"
    if ':' in s:
        parts = s.split(':')
        try:
            partsf = [float(p) for p in parts]
            if len(partsf) == 2:
                return partsf[0] * 60 + partsf[1]
            if len(partsf) == 3:
                return partsf[0] * 3600 + partsf[1] * 60 + partsf[2]
        except:
            pass
    try:
        return float(s)
    except:
        return np.nan

def try_int_port(x):
    if pd.isnull(x):
        return np.nan
    s = str(x).strip()
    # some ports may be "10000_214" style; extract trailing digits if numeric
    if s.isdigit():
        return int(s)
    # try last chunk after '_' if digits
    if '_' in s:
        part = s.split('_')[-1]
        if part.isdigit():
            return int(part)
    # fallback: try to parse
    try:
        return int(float(s))
    except:
        return np.nan

# --- heuristic attack signatures and mapping ---
ATTACK_SIGNATURES = {
    'port_scan': 'Multiple ports scanned with many single-packet attempts (scan behavior).',
    'ssh_bruteforce': 'Repeated small connections to SSH (22) consistent with brute-force attempts.',
    'telnet_scan': 'Access attempts to Telnet (23) — suspicious legacy traffic.',
    'smb_bruteforce': 'SMB attempts (445) potentially brute-force.',
    'web_ddos': 'Very high volume toward web ports (80/443/8080) — possible DDoS.',
    'icmp_flood': 'ICMP floods or abnormal ICMP traffic patterns.',
    'dns_amplification': 'UDP DNS traffic patterns (amplification).',
    'malware_c2': 'Low-and-slow C2-like traffic (periodic small connections to uncommon ports).',
    'data_exfiltration': 'Large data transfers to external endpoints (possible exfiltration).',
    'normal': 'Benign/normal activity.',
    'unknown': 'Not classified by heuristics.'
}

def rule_label_row(row):
    proto = str(row.get('Proto', '')).upper() if not pd.isnull(row.get('Proto')) else ''
    dst = row.get('Dst_Pt_num', np.nan)
    pk = row.get('Packets_int', 0) or 0
    b = row.get('Bytes_int', 0) or 0
    dur = row.get('Duration_sec', 0) or 0
    flags = str(row.get('Flags', '')).upper() if not pd.isnull(row.get('Flags')) else ''

    # quick rules
    if proto == 'ICMP':
        return 'icmp_flood'
    if (pk <= 2 and (dur <= 1 or math.isnan(dur))) and ('S' in flags):
        return 'port_scan'
    if dst == 22:
        if pk < 30 and b < 5000:
            return 'ssh_bruteforce'
        return 'ssh_bruteforce'
    if dst == 23:
        return 'telnet_scan'
    if dst == 445:
        return 'smb_bruteforce'
    if dst in (80, 443, 8080):
        if (pk > 10000) or (b > 50_000_000):
            return 'web_ddos'
        return 'normal'
    if proto == 'UDP' and dst == 53:
        if b > 2000:
            return 'dns_amplification'
        return 'unknown'
    if b > 5_000_000 and (not math.isnan(dur) and dur > 10):
        return 'data_exfiltration'
    # fallback
    return 'normal'

# --- CTGAN wrapper (optional) ---
def ctgan_synthesize(df_subset, n_samples, categorical_columns=None):
    """
    Fit CTGAN to df_subset and sample n_samples rows. If CTGAN not available or fails,
    return an empty DataFrame so caller can fallback.
    """
    if not USE_CTGAN or n_samples <= 0 or len(df_subset) < 10:
        return pd.DataFrame()
    # copy and convert categorical cols to string
    dfct = df_subset.copy()
    if categorical_columns is None:
        categorical_columns = dfct.select_dtypes(include=['object', 'category']).columns.tolist()
    for c in categorical_columns:
        if c in dfct.columns:
            dfct[c] = dfct[c].astype(str).fillna('NA')
    try:
        ct = CTGAN(epochs=300, batch_size=500)
        ct.fit(dfct)
        sampled = ct.sample(n_samples)
        # Try to preserve column set
        sampled = sampled[df_subset.columns.intersection(sampled.columns)]
        # reconnect missing columns
        for c in df_subset.columns:
            if c not in sampled.columns:
                sampled[c] = pd.NA
        sampled = sampled[df_subset.columns]
        return sampled
    except Exception as e:
        print("[!] CTGAN failed:", e)
        return pd.DataFrame()

# --- balancing helpers ---
def make_balanced(df, method='undersample', target_per_class=None, target_size=None, synth_categorical_cols=None):
    """
    Return a new DataFrame balanced according to 'method':
      - undersample: reduce each class to target_per_class (if None -> min_class)
      - oversample  : upsample (sample with replacement) each class to target_per_class (if None -> max_class)
      - synthesize  : use CTGAN per-class to synthesize until target_size is reached (requires CTGAN)
    """

    df = df.copy()
    classes = df['attackType'].fillna('unknown')
    counts = classes.value_counts().to_dict()
    unique_cls = sorted(counts.keys())
    n_classes = len(unique_cls)

    # default target_per_class heuristics
    if target_per_class is None and method in ('undersample', 'oversample'):
        if method == 'undersample':
            target_per_class = min(counts.values())
        else:
            target_per_class = max(counts.values())

    if method in ('undersample', 'oversample'):
        parts = []
        for c in unique_cls:
            group = df[df['attackType'] == c]
            if method == 'undersample':
                parts.append(group.sample(n=min(len(group), int(target_per_class)), random_state=RND))
            else:
                # oversample to target_per_class
                if len(group) == 0:
                    continue
                if len(group) >= int(target_per_class):
                    parts.append(group.sample(n=int(target_per_class), random_state=RND))
                else:
                    extra = group.sample(n=int(target_per_class) - len(group), replace=True, random_state=RND)
                    parts.append(pd.concat([group, extra], ignore_index=True))
        balanced = pd.concat(parts, ignore_index=True).sample(frac=1.0, random_state=RND).reset_index(drop=True)
        return balanced

    elif method == 'synthesize':
        # require target_size to be set
        if target_size is None:
            raise ValueError("method=synthesize requires --target-size")
        current = len(df)
        if current >= target_size:
            # simply return df (or downsample to target)
            return df.sample(n=target_size, random_state=RND).reset_index(drop=True)
        need = target_size - current
        # allocate deficits proportional to inverse freq (boost rare classes)
        invp = {c: 1.0 / (counts.get(c, 0) + 1) for c in unique_cls}
        s = sum(invp.values())
        allocation = {c: int(round((invp[c] / s) * need)) for c in unique_cls}
        # fix rounding deficits
        while sum(allocation.values()) < need:
            # add 1 to smallest class allocation each loop
            cls_sorted = sorted(allocation.items(), key=lambda x: allocation[x[0]])
            allocation[cls_sorted[0][0]] += 1
        synth_parts = []
        numeric_cols = ['Bytes_int', 'Packets_int', 'Duration_sec']
        for c, nmake in allocation.items():
            group = df[df['attackType'] == c]
            if len(group) < 5 or not USE_CTGAN:
                # fallback to sampling with jitter (simple synthetic)
                sampled = group.sample(n=nmake, replace=True, random_state=RND).reset_index(drop=True)
                # small jitter on numeric fields
                for col in numeric_cols:
                    if col in sampled.columns:
                        sampled[col] = (sampled[col].fillna(0).astype(float) * (1 + np.random.normal(0, 0.05, size=len(sampled))))
                sampled['attackType'] = c
                synth_parts.append(sampled)
            else:
                # try CTGAN on group with numeric + some categoricals
                cols_for_ct = list(group.columns)
                # For stability, select a small subset
                if len(cols_for_ct) > 25:
                    cols_for_ct = numeric_cols + ['Proto', 'Src IP Addr', 'Dst IP Addr', 'Dst Pt', 'Flags', 'class']
                    cols_for_ct = [x for x in cols_for_ct if x in group.columns]
                try:
                    sampled = ctgan_synthesize(group[cols_for_ct], nmake, categorical_columns=[c for c in cols_for_ct if group[c].dtype == 'object'])
                    if sampled.empty:
                        sampled = group.sample(n=nmake, replace=True, random_state=RND)
                except Exception:
                    sampled = group.sample(n=nmake, replace=True, random_state=RND)
                # Ensure attackType set
                sampled['attackType'] = c
                synth_parts.append(sampled)
        if synth_parts:
            synth_df = pd.concat(synth_parts, ignore_index=True)
        else:
            synth_df = pd.DataFrame(columns=df.columns)
        combined = pd.concat([df, synth_df], ignore_index=True).sample(frac=1.0, random_state=RND).reset_index(drop=True)
        # If slightly overshot, trim
        if len(combined) > target_size:
            combined = combined.sample(n=target_size, random_state=RND).reset_index(drop=True)
        return combined
    else:
        raise ValueError("Unknown method: " + str(method))

# --- main pipeline ---
def prepare(input_csv, out_minimal='logs_clean_minimal.csv', out_full='logs_clean_full.csv',
            out_balanced='logs_balanced.csv', balance_method=None, target_size=None, target_per_class=None,
            keep_helper_cols=False, split_train_test=False, test_size=0.2):
    print("[i] Loading", input_csv)
    df = load_csv_autodetect(input_csv)
    # normalize columns
    df.columns = [c.strip() for c in df.columns]

    # Ensure columns exist and consistent naming
    # Keep original columns list for minimal output
    original_columns = df.columns.tolist()

    # Add parsed columns
    print("[i] Parsing Bytes, Packets, Duration, Ports ...")
    if 'Bytes' in df.columns:
        df['Bytes_int'] = df['Bytes'].apply(parse_bytes_cell)
    else:
        df['Bytes_int'] = np.nan

    if 'Packets' in df.columns:
        df['Packets_int'] = df['Packets'].apply(parse_packets_cell)
    else:
        df['Packets_int'] = np.nan

    if 'Duration' in df.columns:
        df['Duration_sec'] = df['Duration'].apply(parse_duration_cell)
    else:
        df['Duration_sec'] = np.nan

    # Ports
    if 'Dst Pt' in df.columns:
        df['Dst_Pt_num'] = df['Dst Pt'].apply(try_int_port)
    else:
        df['Dst_Pt_num'] = np.nan
    if 'Src Pt' in df.columns:
        df['Src_Pt_num'] = df['Src Pt'].apply(try_int_port)
    else:
        df['Src_Pt_num'] = np.nan

    # Proto cleaned
    if 'Proto' in df.columns:
        df['Proto_clean'] = df['Proto'].astype(str).str.strip().str.upper()
    else:
        df['Proto_clean'] = ''

    # Apply rule-based attackType labeling (keeps preexisting attackType if present and non-empty)
    print("[i] Assigning attackType heuristically ...")
    if 'attackType' not in df.columns:
        df['attackType'] = pd.NA

    # preserve preexisting non-empty types
    def assign_attack_type(r):
        if pd.notnull(r.get('attackType')) and str(r.get('attackType')).strip() not in ('', '---'):
            return r.get('attackType')
        return rule_label_row(r)

    df['attackType'] = df.apply(assign_attack_type, axis=1)
    # ensure string
    df['attackType'] = df['attackType'].fillna('unknown').astype(str)

    # If many 'unknown', try clustering numeric features to infer more nuanced types
    unknown_mask = df['attackType'].isin(['unknown'])
    if unknown_mask.sum() > 200:
        print("[i] Clustering unknown rows to infer subtypes ...")
        numeric_for_clust = df[['Bytes_int', 'Packets_int', 'Duration_sec']].fillna(0).astype(float)
        try:
            k = min(6, max(3, unknown_mask.sum() // 5000 + 3))
            km = KMeans(n_clusters=k, random_state=RND, n_init=10)
            km.fit(np.log1p(numeric_for_clust[unknown_mask]))
            labels = km.predict(np.log1p(numeric_for_clust[unknown_mask]))
            df.loc[unknown_mask, 'cluster'] = labels
            # map cluster to a more descriptive attackType
            for cl in sorted(df.loc[unknown_mask, 'cluster'].unique()):
                sub = df.loc[df['cluster'] == cl]
                b_mean = sub['Bytes_int'].mean() or 0
                p_mean = sub['Packets_int'].mean() or 0
                d_mean = sub['Duration_sec'].mean() or 0
                # heuristic mapping
                if p_mean < 5 and d_mean < 1:
                    newtype = 'port_scan'
                elif b_mean > 10_000_000:
                    newtype = 'data_exfiltration'
                elif d_mean > 20 and p_mean < 50:
                    newtype = 'malware_c2'
                else:
                    newtype = 'unknown'
                df.loc[df['cluster'] == cl, 'attackType'] = newtype
        except Exception as e:
            print("[!] Clustering failed:", e)

    # Build attackID & attackDescription mapping
    unique_types = sorted(df['attackType'].astype(str).unique())
    type_to_id = {t: f"A{idx+1:05d}" for idx, t in enumerate(unique_types)}
    type_to_desc = {t: ATTACK_SIGNATURES.get(t, "Inferred: " + t) for t in unique_types}
    df['attackID'] = df['attackType'].map(type_to_id)
    df['attackDescription'] = df['attackType'].map(type_to_desc)

    # Save full with helpers
    print("[i] Writing full enhanced file:", out_full)
    df.to_csv(out_full, index=False)

    # Create minimal (original columns + attackType/ID/desc)
    print("[i] Creating minimal file (original columns + attack metadata):", out_minimal)
    minimal_cols = original_columns[:]  # copy
    # add attack columns at end
    for c in ['attackType', 'attackID', 'attackDescription']:
        if c not in minimal_cols:
            minimal_cols.append(c)
    minimal_df = df[minimal_cols]
    minimal_df.to_csv(out_minimal, index=False)

    # Optionally create balanced dataset
    balanced_df = None
    if balance_method:
        print(f"[i] Creating balanced dataset method={balance_method} ...")
        balanced_df = make_balanced(df, method=balance_method, target_per_class=target_per_class, target_size=target_size)
        balanced_df.to_csv(out_balanced, index=False)
        print("[i] Balanced dataset saved:", out_balanced)

    # Optionally drop helper columns in final outputs (if requested)
    if not keep_helper_cols:
        # keep only minimal columns saved above; full file already written
        pass

    # Optionally produce train/test split for balanced_df (if produced)
    if split_train_test and balanced_df is not None:
        print("[i] Creating train/test stratified split ...")
        train, test = train_test_split(balanced_df, test_size=test_size, stratify=balanced_df['attackType'], random_state=RND)
        train.to_csv(out_balanced.replace('.csv', '_train.csv'), index=False)
        test.to_csv(out_balanced.replace('.csv', '_test.csv'), index=False)
        print("[i] Train/test saved.")

    print("[i] Done. Outputs:")
    print("   - Minimal:", out_minimal)
    print("   - Full   :", out_full)
    if balance_method:
        print("   - Balanced:", out_balanced)

    return df

# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, help='input CSV (logs.csv)')
    parser.add_argument('--out-minimal', default='logs_clean_minimal.csv', help='minimal output (original cols + attack metadata)')
    parser.add_argument('--out-full', default='logs_clean_full.csv', help='full output (with helper cols)')
    parser.add_argument('--out-balanced', default='logs_balanced.csv', help='balanced dataset output')
    parser.add_argument('--balance-method', choices=['undersample', 'oversample', 'synthesize', None], default=None,
                        help='if set, create balanced dataset using the chosen method')
    parser.add_argument('--target-size', type=int, default=None, help='target total size for synthesize method')
    parser.add_argument('--target-per-class', type=int, default=None, help='target per class for undersample/oversample')
    parser.add_argument('--keep-helper-cols', action='store_true', help='if set, do not remove helper columns from outputs')
    parser.add_argument('--split-train-test', action='store_true', help='if set, create train/test split for balanced dataset')
    parser.add_argument('--test-size', type=float, default=0.2, help='test size fraction for train/test split')
    args = parser.parse_args()

    prepare(args.input, args.out_minimal, args.out_full, args.out_balanced,
            balance_method=args.balance_method, target_size=args.target_size, target_per_class=args.target_per_class,
            keep_helper_cols=args.keep_helper_cols, split_train_test=args.split_train_test, test_size=args.test_size)
