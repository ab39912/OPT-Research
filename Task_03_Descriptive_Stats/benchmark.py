#!/usr/bin/env python3
"""
benchmark.py  (Bonus: Performance Benchmarking)
-----------------------------------------------
Times the three approaches on the same file and prints a comparison table.

We time a comparable unit of work for each: load the file, then compute the
mean of every numeric column. Polars is skipped automatically if it is not
installed, so this runs even in a pure-Python + Pandas environment.

Usage:
    python benchmark.py [CSV] [--repeat N]
"""

import argparse
import os
import statistics
import sys
import time

import datakit as dk


def time_it(fn, repeat):
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return min(times), statistics.mean(times)


def pure_python_job(path):
    import csv
    import math
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

    def job():
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            cols = {h: [] for h in header}
            for row in reader:
                for i, h in enumerate(header):
                    cols[h].append(row[i] if i < len(row) else None)
        for h in header:
            nums = [float(v) for v in cols[h]
                    if not dk.is_missing(v) and dk.try_float(v)]
            if nums:
                _ = math.fsum(nums) / len(nums)
    return job


def pandas_job(path):
    import pandas as pd

    def job():
        df = pd.read_csv(path, dtype=str, low_memory=False)
        for c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().any():
                _ = s.mean()
    return job


def polars_job(path):
    import polars as pl

    def job():
        df = pl.read_csv(path, infer_schema_length=0, ignore_errors=True)
        for c in df.columns:
            s = df[c].cast(pl.Float64, strict=False)
            if s.drop_nulls().len():
                _ = s.mean()
    return job


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", default="fb_ads_president_scored_anon.csv")
    ap.add_argument("--repeat", type=int, default=3)
    args = ap.parse_args()
    if not os.path.exists(args.input):
        sys.exit(f"ERROR: file not found: {args.input}")

    jobs = [("pure_python", pure_python_job)]
    try:
        import pandas  # noqa: F401
        jobs.append(("pandas", pandas_job))
    except ImportError:
        print("[skip] pandas not installed")
    try:
        import polars  # noqa: F401
        jobs.append(("polars", polars_job))
    except ImportError:
        print("[skip] polars not installed")

    print(f"\nFile: {os.path.basename(args.input)}  |  repeats: {args.repeat}\n")
    print(f"{'approach':<14}{'best (s)':>12}{'mean (s)':>12}")
    print("-" * 38)
    best_pp = None
    results = []
    for name, factory in jobs:
        best, mean = time_it(factory(args.input), args.repeat)
        results.append((name, best, mean))
        if name == "pure_python":
            best_pp = best
    for name, best, mean in results:
        speed = f"  ({best_pp / best:4.1f}x vs pure)" if best_pp else ""
        print(f"{name:<14}{best:>12.3f}{mean:>12.3f}{speed}")


if __name__ == "__main__":
    main()
