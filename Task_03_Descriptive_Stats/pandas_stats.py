#!/usr/bin/env python3
"""
pandas_stats.py  (Milestone B — generalized)
------------------------------
Same dataset-level + grouped analysis as pure_python_stats.py, in Pandas.

The three scripts agree because they share datakit.py for every *decision*
(what is missing, what is numeric, which columns are complex, what to derive).
Pandas then executes those decisions with its own vectorized machinery.

Crucially, we do NOT trust pandas' own dtype inference to decide which columns
are "numeric". We apply the same all-or-nothing rule datakit uses, so the
numeric column set is identical across all three scripts.

Usage:
    python pandas_stats.py [CSV] [--group-by COL [COL ...]] [--top N]
"""

import argparse
import os
import sys

import pandas as pd

import datakit as dk

NA_TOKENS = ["", "NA", "N/A", "n/a", "NaN", "nan", "None", "null"]


def load(path):
    # Read everything as string first so our shared classifier — not pandas'
    # inference — decides the types. keep_default_na aligns with datakit tokens.
    return pd.read_csv(path, dtype=str, na_values=NA_TOKENS,
                       keep_default_na=True, low_memory=False)


def classify(df):
    kinds = {}
    for col in df.columns:
        vals = df[col].tolist()
        kinds[col] = dk.classify_column(vals)
    return kinds


def add_derived(df, kinds):
    derived = dk.derived_columns(kinds)
    for new_col, (src, transform) in derived.items():
        fn = dk.TRANSFORMS[transform]
        df[new_col] = df[src].map(lambda v: None if dk.is_missing(v) else fn(v))
        kinds[new_col] = "float" if transform == "range_midpoint" else "integer"
    return list(derived)


def numeric_frame(df, kinds):
    """A float DataFrame of exactly the columns datakit calls numeric."""
    num_cols = [c for c in df.columns if kinds[c] in ("integer", "float")]
    out = df[num_cols].apply(pd.to_numeric, errors="coerce")
    return out


def report_dataset(df, kinds, dataset_name):
    print("=" * 72)
    print(f"DATASET-LEVEL STATISTICS  (pandas)  --  {dataset_name}")
    print("=" * 72)
    print(f"Rows: {len(df):,}    Columns (incl. derived): {df.shape[1]:,}")

    missing = df.isna().sum()
    pct = (missing / len(df) * 100).round(2)
    kind_series = pd.Series(kinds)
    report = pd.DataFrame({"missing": missing, "missing_%": pct,
                           "kind": kind_series})
    print("\nMissing values per column:")
    print(report.to_string())

    num = numeric_frame(df, kinds)
    if not num.empty:
        print("\nNumeric columns (count/mean/min/max/std/median):")
        desc = num.describe().T
        desc["median"] = num.median()
        print(desc[["count", "mean", "min", "max", "std", "median"]]
              .to_string(float_format=lambda x: f"{x:,.4f}"))

    print("\nNon-numeric columns (count/unique/mode/top5):")
    for col in df.columns:
        if kinds[col] in ("integer", "float", "empty"):
            continue
        vc = df[col].value_counts(dropna=True)
        mode_v = vc.index[0] if len(vc) else None
        mode_f = int(vc.iloc[0]) if len(vc) else 0
        print(f"\n--- {col}  [{kinds[col]}] ---")
        print(f"  count : {int(df[col].notna().sum()):,}")
        print(f"  unique: {int(df[col].nunique(dropna=True)):,}")
        print(f"  mode  : {mode_v!r} (freq {mode_f:,})")
        for value, freq in vc.head(5).items():
            shown = (str(value)[:57] + "...") if len(str(value)) > 60 else value
            print(f"      {int(freq):>8,}  {shown}")


def report_grouped(df, kinds, keys, top=10):
    print("\n" + "=" * 72)
    print(f"GROUPED ANALYSIS by {keys}  (pandas)")
    print("=" * 72)
    grp = df.groupby(keys, dropna=False)
    print(f"Number of groups: {grp.ngroups:,}")

    measure = _pick_measure([c for c in df.columns
                             if kinds[c] in ("integer", "float")])
    sizes = grp.size().sort_values(ascending=False)
    print(f"\nTop {top} groups by row count"
          + (f" (measure = {measure})" if measure else "") + ":")

    if measure:
        m = pd.to_numeric(df[measure], errors="coerce")
        agg = df.assign(_m=m).groupby(keys, dropna=False)["_m"].agg(["mean", "sum"])
        joined = sizes.rename("rows").to_frame().join(agg)
        print(joined.head(top).to_string(
            float_format=lambda x: f"{x:,.2f}"))
    else:
        print(sizes.head(top).to_string())


def _pick_measure(numeric_cols):
    # Prefer a spend measure (raw or derived), then any derived midpoint,
    # then the first numeric column.
    for c in numeric_cols:
        if "spend" in c.lower():
            return c
    for c in numeric_cols:
        if c.endswith("__midpoint"):
            return c
    return numeric_cols[0] if numeric_cols else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Path to any well-formed CSV dataset.")
    ap.add_argument("--group-by", nargs="+", action="append", default=None)
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"ERROR: file not found: {args.input}")

    dataset_name = os.path.basename(args.input)
    df = load(args.input)
    kinds = classify(df)
    original_header = list(df.columns)
    add_derived(df, kinds)
    report_dataset(df, kinds, dataset_name)

    sample = {c: df[c].head(3000).tolist() for c in original_header}
    groupings = args.group_by or dk.choose_group_keys(original_header, sample)
    for keys in groupings:
        if any(k not in df.columns for k in keys):
            print(f"\n[skip] grouping {keys}: missing columns")
            continue
        report_grouped(df, kinds, keys, top=args.top)


if __name__ == "__main__":
    main()
