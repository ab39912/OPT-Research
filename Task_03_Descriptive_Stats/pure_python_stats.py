#!/usr/bin/env python3
"""
pure_python_stats.py  (Milestone B — generalized)
-----------------------------------
Descriptive statistics + grouped analysis using ONLY the standard library.

Adds two things over Task 1:
  1. Grouped analysis (by page_id, and by page_id + ad_id).
  2. Automatic cleaning of complex columns: Facebook range dicts become
     <col>__midpoint, list-strings become <col>__n_items. This is what lets
     us compute meaningful spend statistics, and the Pandas/Polars scripts
     derive the exact same companion columns via the shared datakit module.

Usage:
    python pure_python_stats.py [CSV] [--group-by COL [COL ...]] [--top N]

If no CSV path is given it defaults to fb_ads_president_scored_anon.csv.
If --group-by is omitted, sensible keys are chosen automatically
(page_id, then page_id+ad_id for this dataset).
"""

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict

import datakit as dk

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


# --------------------------------------------------------------------------- #
# Load + build column-major view (single pass)
# --------------------------------------------------------------------------- #
def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [row for row in reader]
    return header, rows


def build_columns(header, rows):
    columns = {name: [] for name in header}
    for row in rows:
        for i, name in enumerate(header):
            columns[name].append(row[i] if i < len(row) else None)
    return columns


def add_derived(header, columns):
    """Detect complex columns and append clean numeric companion columns."""
    kinds = {name: dk.classify_column(columns[name]) for name in header}
    derived_spec = dk.derived_columns(kinds)
    for new_col, (src, transform) in derived_spec.items():
        fn = dk.TRANSFORMS[transform]
        columns[new_col] = [fn(v) if not dk.is_missing(v) else None
                            for v in columns[src]]
        header.append(new_col)
        kinds[new_col] = "float" if transform == "range_midpoint" else "integer"
    return kinds, list(derived_spec)


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def numeric_stats(values):
    """count, mean, min, max, std (sample, n-1), median from a list of values."""
    nums = []
    for v in values:
        if v is None or dk.is_missing(v):
            continue
        if isinstance(v, (int, float)):
            nums.append(float(v))
        elif dk.try_float(v):
            nums.append(float(v))
    n = len(nums)
    if n == 0:
        return dict(count=0, mean=None, min=None, max=None, std=None, median=None)
    total = 0.0
    for x in nums:
        total += x
    mean = total / n
    if n > 1:
        sq = 0.0
        for x in nums:
            sq += (x - mean) ** 2
        std = math.sqrt(sq / (n - 1))
    else:
        std = 0.0
    ordered = sorted(nums)
    mid = n // 2
    median = ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2
    return dict(count=n, mean=mean, min=ordered[0], max=ordered[-1],
                std=std, median=median)


def categorical_stats(values):
    present = [str(v).strip() for v in values if not dk.is_missing(v)]
    counter = Counter(present)
    top = counter.most_common(5)
    mode_v, mode_f = (top[0] if top else (None, 0))
    return dict(count=len(present), unique=len(counter),
                mode=mode_v, mode_freq=mode_f, top5=top)


def is_numeric_kind(kind):
    return kind in ("integer", "float")


# --------------------------------------------------------------------------- #
# Reporting: dataset level
# --------------------------------------------------------------------------- #
def fmt(x):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:,.4f}"
    if isinstance(x, int):
        return f"{x:,}"
    return str(x)


def report_dataset(header, columns, kinds, n_rows, dataset_name):
    print("=" * 72)
    print(f"DATASET-LEVEL STATISTICS  (pure Python)  --  {dataset_name}")
    print("=" * 72)
    print(f"Rows: {n_rows:,}    Columns (incl. derived): {len(header):,}")
    print("\nMissing values per column:")
    for name in header:
        miss = sum(1 for v in columns[name] if dk.is_missing(v))
        pct = (miss / n_rows * 100) if n_rows else 0
        print(f"  {name:<48} {miss:>8,}  ({pct:5.2f}%)  [{kinds[name]}]")

    print("\nPer-column statistics:")
    for name in header:
        kind = kinds[name]
        print(f"\n--- {name}  [{kind}] ---")
        if is_numeric_kind(kind):
            s = numeric_stats(columns[name])
            for k in ("count", "mean", "min", "max", "std", "median"):
                print(f"  {k:<7}: {fmt(s[k])}")
        elif kind == "empty":
            print("  (entirely empty)")
        else:
            s = categorical_stats(columns[name])
            print(f"  count : {fmt(s['count'])}")
            print(f"  unique: {fmt(s['unique'])}")
            print(f"  mode  : {s['mode']!r} (freq {fmt(s['mode_freq'])})")
            for value, freq in s["top5"]:
                shown = (value[:57] + "...") if len(value) > 60 else value
                print(f"      {freq:>8,}  {shown}")


# --------------------------------------------------------------------------- #
# Reporting: grouped
# --------------------------------------------------------------------------- #
def group_indices(columns, keys, n_rows):
    """Map each group key tuple -> list of row indices. This is the manual
    equivalent of groupby: bucket rows into dicts keyed by the group columns."""
    buckets = defaultdict(list)
    for i in range(n_rows):
        key = tuple("" if dk.is_missing(columns[k][i]) else str(columns[k][i]).strip()
                    for k in keys)
        buckets[key].append(i)
    return buckets


def report_grouped(header, columns, kinds, keys, n_rows, top=10):
    print("\n" + "=" * 72)
    print(f"GROUPED ANALYSIS by {keys}  (pure Python)")
    print("=" * 72)
    buckets = group_indices(columns, keys, n_rows)
    print(f"Number of groups: {len(buckets):,}")

    # Choose numeric measures to summarize per group.
    numeric_cols = [c for c in header if is_numeric_kind(kinds[c])]
    measure = _pick_measure(numeric_cols)

    # Rank groups by size, show the largest few.
    ordered = sorted(buckets.items(), key=lambda kv: len(kv[1]), reverse=True)
    print(f"\nTop {top} groups by row count"
          + (f" (measure = {measure})" if measure else "") + ":")
    header_line = f"  {'group':<45} {'rows':>8}"
    if measure:
        header_line += f" {'mean':>14} {'sum':>16}"
    print(header_line)
    for key, idxs in ordered[:top]:
        label = " | ".join(key)
        label = (label[:42] + "...") if len(label) > 45 else label
        line = f"  {label:<45} {len(idxs):>8,}"
        if measure:
            vals = [columns[measure][i] for i in idxs]
            s = numeric_stats(vals)
            mean = s["mean"] if s["mean"] is not None else 0.0
            total = mean * s["count"]
            line += f" {mean:>14,.2f} {total:>16,.2f}"
        print(line)


def _pick_measure(numeric_cols):
    """Prefer a spend measure (raw or derived), then any midpoint, then first."""
    for c in numeric_cols:
        if "spend" in c.lower():
            return c
    for c in numeric_cols:
        if c.endswith("__midpoint"):
            return c
    return numeric_cols[0] if numeric_cols else None


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Path to any well-formed CSV dataset.")
    ap.add_argument("--group-by", nargs="+", action="append", default=None,
                    help="Grouping key(s). Repeat the flag for multiple groupings, "
                         "e.g. --group-by page_id --group-by page_id ad_id")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"ERROR: file not found: {args.input}\n"
                 f"Download the dataset and pass its path.")

    dataset_name = os.path.basename(args.input)
    header, rows = load(args.input)
    n_rows = len(rows)
    columns = build_columns(header, rows)
    kinds, derived = add_derived(header, columns)
    if derived:
        print(f"[cleaning] derived columns added: {', '.join(derived)}\n")

    report_dataset(header, columns, kinds, n_rows, dataset_name)

    original_header = header[:len(header) - len(derived)]
    sample = {c: columns[c][:3000] for c in original_header}
    groupings = args.group_by or dk.choose_group_keys(original_header, sample)
    for keys in groupings:
        missing = [k for k in keys if k not in columns]
        if missing:
            print(f"\n[skip] grouping {keys}: missing columns {missing}")
            continue
        report_grouped(header, columns, kinds, keys, n_rows, top=args.top)


if __name__ == "__main__":
    main()
