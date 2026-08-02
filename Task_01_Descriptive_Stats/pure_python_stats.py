#!/usr/bin/env python3
"""
pure_python_stats.py
--------------------
Descriptive statistics for the 2024 Facebook political ads dataset, computed
using ONLY the Python standard library (csv, math, collections, ...).

No pandas, no numpy, no third-party packages.

The point of this script is understanding, not speed. Every statistic here is
computed by hand so that the edge cases pandas hides from you (missing values,
"numeric" columns that contain junk strings, entirely empty columns) have to be
handled explicitly.

Usage:
    python pure_python_stats.py [path/to/data.csv]
    python pure_python_stats.py --input data.csv --group-by page_name

If no path is given, it looks for ./fb_ads_president_scored_anon.csv.
"""

import argparse
import csv
import math
import os
import sys
from collections import Counter

# CSV fields in this dataset can be long (dict-like strings), so lift the limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

# Strings that we treat as "missing" regardless of the column.
MISSING_TOKENS = {"", "na", "n/a", "nan", "none", "null"}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_csv(path):
    """Load a CSV into (header, rows) using the csv module.

    We do NOT split on commas by hand. CSV is deceptively hard: quoted fields,
    embedded commas, and newlines inside fields all break naive .split(',').
    csv.reader handles all of that correctly.
    """
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [row for row in reader]
    return header, rows


def is_missing(value):
    """A cell counts as missing if it is None or a known empty/NA token."""
    return value is None or value.strip().lower() in MISSING_TOKENS


# --------------------------------------------------------------------------- #
# Type inference
# --------------------------------------------------------------------------- #
def try_int(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def try_float(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def looks_like_date(value):
    """Cheap ISO-ish date check: YYYY-MM-DD with plausible parts.

    We deliberately keep this simple (no datetime parsing of every cell) because
    this is only used for *labeling* a column's apparent type, not for math.
    """
    v = value.strip()
    if len(v) < 8 or v.count("-") != 2:
        return False
    parts = v.split("-")
    if len(parts) != 3:
        return False
    y, m, d = parts
    if not (y.isdigit() and m.isdigit() and d[:2].isdigit()):
        return False
    return len(y) == 4 and 1 <= int(m) <= 12 and 1 <= int(d[:2]) <= 31


def infer_type(values):
    """Infer the apparent type of a column from its non-missing values.

    Returns one of: 'empty', 'integer', 'float', 'date', 'string'.
    A column is 'integer' only if EVERY non-missing value parses as an int, etc.
    This "all-or-nothing" rule is what forces honesty: one stray "$1,234.56" in
    an otherwise numeric column demotes it to 'string', which is exactly the
    kind of surprise the manual approach is meant to expose.
    """
    non_missing = [v for v in values if not is_missing(v)]
    if not non_missing:
        return "empty"
    if all(try_int(v) for v in non_missing):
        return "integer"
    if all(try_float(v) for v in non_missing):
        return "float"
    if all(looks_like_date(v) for v in non_missing):
        return "date"
    return "string"


# --------------------------------------------------------------------------- #
# Numeric statistics (computed from scratch)
# --------------------------------------------------------------------------- #
def compute_numeric_stats(values):
    """Descriptive stats for a list of raw string values in a numeric column.

    Non-numeric / missing entries are skipped (and reported via the count).
    Returns a dict; std uses the sample standard deviation (n-1 denominator),
    which matches pandas' default and R's sd().
    """
    nums = [float(v) for v in values if not is_missing(v) and try_float(v)]
    count = len(nums)
    if count == 0:
        return {"count": 0, "mean": None, "min": None, "max": None,
                "std": None, "median": None}

    total = 0.0
    for x in nums:            # sum by hand rather than sum() to stay explicit
        total += x
    mean = total / count

    # Sample standard deviation.
    if count > 1:
        sq = 0.0
        for x in nums:
            sq += (x - mean) ** 2
        std = math.sqrt(sq / (count - 1))
    else:
        std = 0.0

    ordered = sorted(nums)
    mid = count // 2
    if count % 2 == 1:
        median = ordered[mid]
    else:
        median = (ordered[mid - 1] + ordered[mid]) / 2

    return {"count": count, "mean": mean, "min": ordered[0],
            "max": ordered[-1], "std": std, "median": median}


# --------------------------------------------------------------------------- #
# Categorical statistics
# --------------------------------------------------------------------------- #
def compute_categorical_stats(values):
    """Count, unique count, mode + frequency, and top-5 values for a column."""
    present = [v.strip() for v in values if not is_missing(v)]
    counter = Counter(present)
    top = counter.most_common(5)
    mode_value, mode_freq = (top[0] if top else (None, 0))
    return {"count": len(present), "unique": len(counter),
            "mode": mode_value, "mode_freq": mode_freq, "top5": top}


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def fmt(x):
    """Format a number for display; pass through None/strings unchanged."""
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:,.4f}".rstrip("0").rstrip(".") if x != int(x) else f"{int(x):,}"
    return f"{x:,}" if isinstance(x, int) else str(x)


def analyze(header, rows, group_by=None):
    n_rows = len(rows)
    n_cols = len(header)
    # Build column-major view once so we iterate rows a single time.
    columns = {name: [] for name in header}
    for row in rows:
        for i, name in enumerate(header):
            columns[name].append(row[i] if i < len(row) else None)

    print("=" * 70)
    print("DATASET OVERVIEW  (pure Python)")
    print("=" * 70)
    print(f"Total rows:    {n_rows:,}")
    print(f"Total columns: {n_cols:,}")
    print()
    print("Missing values per column:")
    for name in header:
        miss = sum(1 for v in columns[name] if is_missing(v))
        pct = (miss / n_rows * 100) if n_rows else 0
        print(f"  {name:<45} {miss:>8,}  ({pct:5.2f}%)")
    print()

    print("=" * 70)
    print("PER-COLUMN STATISTICS")
    print("=" * 70)
    for name in header:
        col = columns[name]
        col_type = infer_type(col)
        print(f"\n--- {name}  [apparent type: {col_type}] ---")
        if col_type in ("integer", "float"):
            s = compute_numeric_stats(col)
            print(f"  count : {fmt(s['count'])}")
            print(f"  mean  : {fmt(s['mean'])}")
            print(f"  min   : {fmt(s['min'])}")
            print(f"  max   : {fmt(s['max'])}")
            print(f"  std   : {fmt(s['std'])}")
            print(f"  median: {fmt(s['median'])}")
        elif col_type == "empty":
            print("  (column is entirely empty / missing)")
        else:
            s = compute_categorical_stats(col)
            print(f"  count       : {fmt(s['count'])}")
            print(f"  unique      : {fmt(s['unique'])}")
            print(f"  mode        : {s['mode']!r}  (freq {fmt(s['mode_freq'])})")
            print("  top 5 values:")
            for value, freq in s["top5"]:
                shown = (value[:60] + "...") if len(value) > 63 else value
                print(f"      {freq:>8,}  {shown}")

    if group_by and group_by in columns:
        print("\n" + "=" * 70)
        print(f"GROUP-BY: value counts for '{group_by}' (top 15)")
        print("=" * 70)
        counter = Counter(v.strip() for v in columns[group_by] if not is_missing(v))
        for value, freq in counter.most_common(15):
            print(f"  {freq:>8,}  {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?",
                        default="fb_ads_president_scored_anon.csv",
                        help="Path to the CSV file.")
    parser.add_argument("--input", dest="input_flag", default=None,
                        help="Alternative way to pass the input path.")
    parser.add_argument("--group-by", default=None,
                        help="Optional column to produce extra value counts for "
                             "(e.g. page_name).")
    args = parser.parse_args()

    path = args.input_flag or args.input
    if not os.path.exists(path):
        sys.exit(f"ERROR: file not found: {path}\n"
                 f"Download the dataset and pass its path, e.g.\n"
                 f"    python pure_python_stats.py path/to/{os.path.basename(path)}")

    header, rows = load_csv(path)
    analyze(header, rows, group_by=args.group_by)


if __name__ == "__main__":
    main()
