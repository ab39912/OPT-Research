#!/usr/bin/env python3
"""
visualize.py  (Bonus: Visualizations)
-------------------------------------
Charts that support a narrative about the 2024 Facebook ad data. Uses the
shared datakit cleaning so the spend figures match the stats scripts.

Outputs PNGs into ./images/.

Usage:
    python visualize.py [CSV]
"""

import argparse
import os
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import datakit as dk

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", nargs="?", default="fb_ads_president_scored_anon.csv")
    args = ap.parse_args()
    if not os.path.exists(args.input):
        sys.exit(f"ERROR: file not found: {args.input}")
    os.makedirs(OUTDIR, exist_ok=True)

    df = pd.read_csv(args.input, dtype=str, low_memory=False)

    # Spend column: some files store a plain integer (estimated_spend), older
    # ones a range dict (spend). Handle either.
    if "estimated_spend" in df.columns:
        df["spend_mid"] = pd.to_numeric(df["estimated_spend"], errors="coerce")
    elif "spend" in df.columns:
        df["spend_mid"] = pd.to_numeric(
            df["spend"].map(lambda v: None if dk.is_missing(v)
                            else dk.parse_range_midpoint(v)), errors="coerce")
    else:
        df["spend_mid"] = pd.NA

    # Advertiser identity: page_name if present, else the (hashed) page_id.
    id_col = "page_name" if "page_name" in df.columns else (
        "page_id" if "page_id" in df.columns else None)

    # Top spenders.
    if id_col:
        top = (df.groupby(id_col)["spend_mid"].sum()
                 .sort_values(ascending=False).head(10) / 1e6)
        labels = [str(x)[:14] + "…" if len(str(x)) > 15 else str(x)
                  for x in top.index]
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh(labels[::-1], top.values[::-1], color="#2c3e50")
        ax.set_title(f"Top 10 advertisers by estimated total spend (by {id_col})")
        ax.set_xlabel("Estimated spend ($M)")
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, "top_spenders.png"), dpi=130)
        plt.close(fig)

    # Spend over time.
    if "ad_creation_time" in df.columns:
        df["created"] = pd.to_datetime(df["ad_creation_time"], errors="coerce")
        d24 = df[df["created"] >= "2024-01-01"]
        monthly = d24.set_index("created")["spend_mid"].resample("MS").sum() / 1e6
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.plot(monthly.index, monthly.values, marker="o", color="#c0392b")
        ax.set_title("Estimated Facebook political ad spend by month (2024)")
        ax.set_ylabel("Estimated spend ($M)")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, "spend_over_time.png"), dpi=130)
        plt.close(fig)

    # Candidate mentions.
    if "illuminating_mentions" in df.columns:
        import ast
        counter = Counter()
        for cell in df["illuminating_mentions"].dropna():
            try:
                for name in ast.literal_eval(cell):
                    counter[name] += 1
            except (ValueError, SyntaxError, TypeError):
                pass
        if counter:
            top_m = counter.most_common(10)[::-1]
            fig, ax = plt.subplots(figsize=(9, 5))
            ax.barh([k for k, _ in top_m], [v for _, v in top_m], color="#27ae60")
            ax.set_title("Most-mentioned figures across ads")
            ax.set_xlabel("Number of ads mentioning")
            fig.tight_layout()
            fig.savefig(os.path.join(OUTDIR, "candidate_mentions.png"), dpi=130)
            plt.close(fig)

    print(f"Saved charts to {OUTDIR}/")


if __name__ == "__main__":
    main()
