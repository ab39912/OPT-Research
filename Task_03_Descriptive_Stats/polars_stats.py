#!/usr/bin/env python3
"""
polars_stats.py  (Milestone B — generalized)
------------------------------
Same dataset-level + grouped analysis as the other two scripts, in Polars.

Design notes / why this looks different from the Pandas script:
  * Polars is strict about types and expression-based. We read every column as
    a string (infer_schema_length=0) so that the SHARED datakit classifier —
    not Polars' own inference — decides types, exactly as the Pandas script
    does. That is what keeps all three numerically identical.
  * Polars' Series.std() uses the sample standard deviation (ddof=1) by
    default, matching Pandas and our pure-Python implementation.
  * value_counts / n_unique / null_count are the Polars-native equivalents of
    the Pandas calls.

Tested API target: Polars >= 0.20 (uses group_by, pl.len, map_elements).
NOTE: this script was authored against the documented Polars API; run it once
locally to confirm on your installed version (see requirements.txt).

Usage:
    python polars_stats.py [CSV] [--group-by COL [COL ...]] [--top N]
"""

import argparse
import os
import sys

import polars as pl

import datakit as dk

NA_TOKENS = ["", "NA", "N/A", "n/a", "NaN", "nan", "None", "null"]


def load(path):
    # infer_schema_length=0 -> read all columns as strings (Utf8), so our
    # shared classifier decides types. null_values aligns nulls with datakit.
    return pl.read_csv(path, infer_schema_length=0, null_values=NA_TOKENS,
                       ignore_errors=True)


def classify(df):
    return {col: dk.classify_column(df[col].to_list()) for col in df.columns}


def add_derived(df, kinds):
    derived = dk.derived_columns(kinds)
    for new_col, (src, transform) in derived.items():
        fn = dk.TRANSFORMS[transform]
        dtype = pl.Float64 if transform == "range_midpoint" else pl.Int64
        df = df.with_columns(
            pl.col(src)
            .map_elements(lambda v, _fn=fn: (None if dk.is_missing(v) else _fn(v)),
                          return_dtype=pl.Float64)
            .alias(new_col)
        )
        kinds[new_col] = "float" if transform == "range_midpoint" else "integer"
    return df, list(derived)


def numeric_cols(df, kinds):
    return [c for c in df.columns if kinds[c] in ("integer", "float")]


def report_dataset(df, kinds, dataset_name):
    print("=" * 72)
    print(f"DATASET-LEVEL STATISTICS  (polars)  --  {dataset_name}")
    print("=" * 72)
    print(f"Rows: {df.height:,}    Columns (incl. derived): {df.width:,}")

    # Null counts per column (null_count() -> single-row frame).
    nulls = df.null_count().to_dicts()[0]
    print("\nMissing values per column:")
    for col in df.columns:
        miss = nulls.get(col, 0)
        pct = (miss / df.height * 100) if df.height else 0
        print(f"  {col:<48} {miss:>8,}  ({pct:5.2f}%)  [{kinds[col]}]")

    ncols = numeric_cols(df, kinds)
    if ncols:
        print("\nNumeric columns (count/mean/min/max/std/median):")
        num = df.select([pl.col(c).cast(pl.Float64, strict=False) for c in ncols])
        for c in ncols:
            s = num[c]
            count = s.drop_nulls().len()
            mean = s.mean()
            mn = s.min()
            mx = s.max()
            std = s.std()  # ddof=1 by default
            med = s.median()
            print(f"  {c:<45} count={count:,} mean={_f(mean)} "
                  f"min={_f(mn)} max={_f(mx)} std={_f(std)} median={_f(med)}")

    print("\nNon-numeric columns (count/unique/mode/top5):")
    for col in df.columns:
        if kinds[col] in ("integer", "float", "empty"):
            continue
        s = df[col]
        non_null = s.drop_nulls()
        vc = non_null.value_counts(sort=True)
        # value_counts returns columns [<col>, "count"] in modern Polars.
        count_col = "count" if "count" in vc.columns else vc.columns[-1]
        print(f"\n--- {col}  [{kinds[col]}] ---")
        print(f"  count : {non_null.len():,}")
        print(f"  unique: {s.n_unique():,}")
        if vc.height:
            top = vc.head(5)
            mode_v = top[col][0]
            mode_f = top[count_col][0]
            print(f"  mode  : {mode_v!r} (freq {mode_f:,})")
            for i in range(top.height):
                value = str(top[col][i])
                freq = top[count_col][i]
                shown = (value[:57] + "...") if len(value) > 60 else value
                print(f"      {freq:>8,}  {shown}")


def report_grouped(df, kinds, keys, top=10):
    print("\n" + "=" * 72)
    print(f"GROUPED ANALYSIS by {keys}  (polars)")
    print("=" * 72)

    measure = _pick_measure(numeric_cols(df, kinds))
    aggs = [pl.len().alias("rows")]
    if measure:
        aggs += [
            pl.col(measure).cast(pl.Float64, strict=False).mean().alias("mean"),
            pl.col(measure).cast(pl.Float64, strict=False).sum().alias("sum"),
        ]
    grouped = df.group_by(keys).agg(aggs).sort("rows", descending=True)
    print(f"Number of groups: {grouped.height:,}")
    print(f"\nTop {top} groups by row count"
          + (f" (measure = {measure})" if measure else "") + ":")
    with pl.Config(tbl_rows=top, fmt_str_lengths=50):
        print(grouped.head(top))


def _pick_measure(cols):
    # Prefer a spend measure (raw or derived), then any derived midpoint,
    # then the first numeric column.
    for c in cols:
        if "spend" in c.lower():
            return c
    for c in cols:
        if c.endswith("__midpoint"):
            return c
    return cols[0] if cols else None


def _f(x):
    return "n/a" if x is None else f"{x:,.4f}"


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
    df, _ = add_derived(df, kinds)

    report_dataset(df, kinds, dataset_name)

    sample = {c: df[c].head(3000).to_list() for c in original_header}
    groupings = args.group_by or dk.choose_group_keys(original_header, sample)
    for keys in groupings:
        if any(k not in df.columns for k in keys):
            print(f"\n[skip] grouping {keys}: missing columns")
            continue
        report_grouped(df, kinds, keys, top=args.top)


if __name__ == "__main__":
    main()
