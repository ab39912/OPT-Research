#!/usr/bin/env python3
"""
visualize.py  (Bonus 1)
-----------------------
Generates the charts referenced in the README / FINDINGS.

Two of the most analytically important columns (spend, impressions) are NOT
plain numbers in this dataset: Facebook reports them as bounded ranges stored
as dict-like strings, e.g.

    {'lower_bound': '200', 'upper_bound': '299'}

For any economic analysis we collapse each range to its midpoint. This is a
modeling choice, not a fact in the data, and it is documented as such in
FINDINGS.md.

Outputs PNGs into ./images/.

Usage:
    python visualize.py [path/to/data.csv]
"""

import argparse
import ast
import os
import sys

import matplotlib
matplotlib.use("Agg")  # headless / no display needed
import matplotlib.pyplot as plt
import pandas as pd

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


def range_midpoint(cell):
    """Collapse a {'lower_bound':.., 'upper_bound':..} string to its midpoint."""
    try:
        d = ast.literal_eval(cell)
        lo = d.get("lower_bound")
        up = d.get("upper_bound")
        lo = float(lo) if lo not in (None, "") else None
        up = float(up) if up not in (None, "") else lo
        if lo is None:
            return None
        return (lo + up) / 2 if up is not None else lo
    except (ValueError, SyntaxError, AttributeError, TypeError):
        return None


def mentions_list(cell):
    try:
        return list(ast.literal_eval(cell))
    except (ValueError, SyntaxError, TypeError):
        return []


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?",
                        default="fb_ads_president_scored_anon.csv")
    args = parser.parse_args()
    if not os.path.exists(args.input):
        sys.exit(f"ERROR: file not found: {args.input}")

    os.makedirs(OUTDIR, exist_ok=True)
    df = pd.read_csv(args.input, low_memory=False)
    df["spend_mid"] = df["spend"].map(range_midpoint)
    df["creation"] = pd.to_datetime(df["ad_creation_time"], errors="coerce")

    # 1. Estimated spend over time (2024) ---------------------------------- #
    d24 = df[df["creation"] >= "2024-01-01"].copy()
    monthly = (d24.set_index("creation")["spend_mid"]
                  .resample("MS").sum() / 1e6)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(monthly.index, monthly.values, marker="o", color="#c0392b")
    ax.set_title("Estimated Facebook political ad spend by month (2024)")
    ax.set_ylabel("Estimated spend ($M, range midpoints)")
    ax.set_xlabel("Month of ad creation")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "spend_over_time.png"), dpi=130)
    plt.close(fig)

    # 2. Top 10 spenders --------------------------------------------------- #
    top = (df.groupby("page_name")["spend_mid"].sum()
             .sort_values(ascending=False).head(10) / 1e6)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top.index[::-1], top.values[::-1], color="#2c3e50")
    ax.set_title("Top 10 advertisers by estimated total spend")
    ax.set_xlabel("Estimated spend ($M, range midpoints)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "top_spenders.png"), dpi=130)
    plt.close(fig)

    # 3. Candidate mention frequency --------------------------------------- #
    from collections import Counter
    counter = Counter()
    for cell in df["illuminating_mentions"].dropna():
        for name in mentions_list(cell):
            counter[name] += 1
    top_m = counter.most_common(10)
    labels = [k for k, _ in top_m][::-1]
    values = [v for _, v in top_m][::-1]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(labels, values, color="#27ae60")
    ax.set_title("Most-mentioned figures across ads")
    ax.set_xlabel("Number of ads mentioning")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "candidate_mentions.png"), dpi=130)
    plt.close(fig)

    # 4. Spend distribution (log scale) ------------------------------------ #
    fig, ax = plt.subplots(figsize=(9, 4.5))
    vals = df["spend_mid"].dropna()
    vals = vals[vals > 0]
    ax.hist(vals, bins=60)
    ax.set_yscale("log")
    ax.set_title("Distribution of per-ad estimated spend (log count)")
    ax.set_xlabel("Estimated spend per ad ($, range midpoint)")
    ax.set_ylabel("Number of ads (log)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "spend_distribution.png"), dpi=130)
    plt.close(fig)

    print(f"Saved 4 charts to {OUTDIR}/")


if __name__ == "__main__":
    main()
