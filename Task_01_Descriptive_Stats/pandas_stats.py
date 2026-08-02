#!/usr/bin/env python3
"""
pandas_stats.py
---------------
The same descriptive analysis as pure_python_stats.py, done with pandas.

The comparison between the two scripts is the point of the exercise, so this
file deliberately mirrors the structure of the pure-Python one: overview,
per-column stats, then optional group-by. Where pandas makes a decision
silently that the manual version had to make explicitly, a comment flags it.

Usage:
    python pandas_stats.py [path/to/data.csv]
    python pandas_stats.py --input data.csv --group-by page_name
"""

import argparse
import os
import sys

import pandas as pd

# Tokens pandas should treat as NaN on load. Note: this is one of the "silent
# decisions" the pure-Python version had to make by hand (see MISSING_TOKENS
# there). Here we make it explicit so the two scripts agree.
NA_TOKENS = ["", "NA", "N/A", "n/a", "NaN", "nan", "None", "null"]


def load(path):
    # low_memory=False avoids mixed-dtype chunk warnings on this wide file.
    return pd.read_csv(path, na_values=NA_TOKENS, keep_default_na=True,
                       low_memory=False)


def overview(df):
    print("=" * 70)
    print("DATASET OVERVIEW  (pandas)")
    print("=" * 70)
    print(f"Total rows:    {df.shape[0]:,}")
    print(f"Total columns: {df.shape[1]:,}")
    print()
    print("df.info():")
    df.info()
    print()

    missing = df.isna().sum()
    pct = (missing / len(df) * 100).round(2)
    report = pd.DataFrame({"missing": missing, "missing_%": pct})
    print("Missing values per column:")
    print(report.to_string())
    print()


def numeric_section(df):
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        print("(no columns were inferred as numeric)")
        return
    print("=" * 70)
    print("NUMERIC COLUMNS  (describe + median + std)")
    print("=" * 70)
    # describe() gives count/mean/std/min/quartiles/max; we add median for a
    # 1:1 match with the pure-Python output. pandas std is sample std (ddof=1).
    desc = numeric.describe().T
    desc["median"] = numeric.median()
    cols = ["count", "mean", "min", "max", "std", "median"]
    print(desc[cols].to_string(float_format=lambda x: f"{x:,.4f}"))
    print()


def categorical_section(df):
    non_numeric = df.select_dtypes(exclude="number")
    if non_numeric.empty:
        return
    print("=" * 70)
    print("NON-NUMERIC COLUMNS  (count / unique / mode / top 5)")
    print("=" * 70)
    for name in non_numeric.columns:
        col = df[name]
        vc = col.value_counts(dropna=True)
        mode_val = vc.index[0] if len(vc) else None
        mode_freq = int(vc.iloc[0]) if len(vc) else 0
        print(f"\n--- {name} ---")
        print(f"  count : {int(col.notna().sum()):,}")
        print(f"  unique: {int(col.nunique(dropna=True)):,}")
        print(f"  mode  : {mode_val!r}  (freq {mode_freq:,})")
        print("  top 5 values:")
        for value, freq in vc.head(5).items():
            shown = (str(value)[:60] + "...") if len(str(value)) > 63 else value
            print(f"      {int(freq):>8,}  {shown}")
    print()

    # describe() on object columns is a compact alternative pandas offers "for
    # free". The pure-Python version had no such shortcut and had to build it.
    print("df.describe(include='object')  [pandas shortcut]:")
    print(non_numeric.describe(include="object").T.to_string())
    print()


def group_by_section(df, group_by):
    if group_by and group_by in df.columns:
        print("=" * 70)
        print(f"GROUP-BY: value counts for '{group_by}' (top 15)")
        print("=" * 70)
        print(df[group_by].value_counts(dropna=True).head(15).to_string())
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?",
                        default="fb_ads_president_scored_anon.csv",
                        help="Path to the CSV file.")
    parser.add_argument("--input", dest="input_flag", default=None,
                        help="Alternative way to pass the input path.")
    parser.add_argument("--group-by", default=None,
                        help="Optional column for extra value counts.")
    args = parser.parse_args()

    path = args.input_flag or args.input
    if not os.path.exists(path):
        sys.exit(f"ERROR: file not found: {path}\n"
                 f"Download the dataset and pass its path, e.g.\n"
                 f"    python pandas_stats.py path/to/{os.path.basename(path)}")

    df = load(path)
    overview(df)
    numeric_section(df)
    categorical_section(df)
    group_by_section(df, args.group_by)


if __name__ == "__main__":
    main()
