# Task_03_Descriptive_Stats (Milestone B)

A **dataset-agnostic descriptive-statistics system**. The same three scripts
(pure Python, Pandas, Polars) run on *any* of the three 2024 election social
media datasets — Facebook Ads, Facebook Posts, Twitter/X Posts — and on most
well-formed CSVs generally, with **no per-dataset hardcoding**. A fourth script
compares shared columns across the platforms.

## What makes it a system, not three scripts

Every implementation imports one standard-library-only module, `datakit.py`,
which owns the decisions that must be schema-independent and identical across
libraries:

- **Dynamic type detection** — no fixed schema is assumed. Each column is
  classified from its values (`integer`, `float`, `date`, `range`, `list`,
  `string`, `empty`) by an all-or-nothing numeric rule, so Pandas' and Polars'
  own inference never gets a chance to disagree.
- **Missing-value handling** — one shared null-token set.
- **Complex-column cleaning** — list-strings get element-count companions; range
  dicts (if present) get midpoint companions; nested dicts are recognized and
  left categorical. This fired differently on each file, which is the point.
- **Data-aware group-key selection** — for an unknown file the system samples the
  data and picks useful groupings, preferring an account/owner identifier plus a
  categorical dimension, while skipping constant columns, per-row IDs, binary
  flags, dates, and complex columns. That is why it chooses `page_id` for ads,
  `Facebook_Id` + `Page Category` for FB posts, and `lang` + `source` for tweets
  without being told.

Because all of that lives in one place, pointing the system at a new file "just
works," and the same numbers come out of all three libraries.

```
datakit.py            shared, stdlib-only detection + cleaning (the "system")
pure_python_stats.py  per-dataset stats + grouped analysis, stdlib only
pandas_stats.py       same, Pandas
polars_stats.py       same, Polars
cross_dataset.py      shared-column comparison across N files -> CROSS_DATASET.md
benchmark.py          bonus: times the three approaches
```

## Getting the data

Download the three CSVs from the task's Google Drive link and place them
anywhere. Every script takes the path(s) as arguments. Nothing is committed.

## How to run

Python 3.9+. The same command works on any of the three files:

```bash
python pure_python_stats.py /path/to/2024_fb_ads_president_scored_anon.csv
python pandas_stats.py      /path/to/2024_fb_posts_president_scored_anon.csv
python polars_stats.py      /path/to/2024_tw_posts_president_scored_anon.csv
```

Groupings auto-detect; override with the repeatable `--group-by` flag.

**Cross-platform comparison** (the Milestone-B deliverable):

```bash
python cross_dataset.py \
    /path/to/2024_fb_ads_president_scored_anon.csv \
    /path/to/2024_fb_posts_president_scored_anon.csv \
    /path/to/2024_tw_posts_president_scored_anon.csv \
    --labels ads fb_posts tw_posts \
    --out CROSS_DATASET.md
```

## Findings per dataset

**Facebook Ads** (246,745 rows). ~$261.9M estimated spend, extremely
concentrated — the top `page_id` alone is ~$82.8M (about a third of the total).
Per-ad spend is heavily right-skewed (median **$49**, mean **$1,061**, max
**$474,999**), and monthly spend ramps from ~$6M early in 2024 to **~$85M in
October** before collapsing in November. Trump is the most-mentioned figure
(~78k ads) despite the top-spending pages being Democratic.

**Facebook Posts** (19,009 rows). Organic engagement is even more skewed than ad
spend: **Total Interactions** median **133** vs mean **2,210** (max ~470k); likes
median 139 / mean 2,378. Posts come mostly from `PERSON` and `POLITICIAN`
page categories, and `Link` and `Photo` are the most common post types. There is
a real data-quality flaw here — a malformed header fuses two columns
(`illuminating_scored_messageelection_integrity_Truth_illuminating`).

**Twitter/X Posts** (27,304 rows). The most extreme distributions of all:
`likeCount` median **1,406** but mean **6,914** (max ~915k), and `viewCount`
median ~71k against a max of **333 million**. Content is ~99.9% English; the top
posting clients are Twitter Web App and iPhone, with Sprout Social indicating
scheduled/organizational posting.

## Cross-dataset comparison

Full detail in [`CROSS_DATASET.md`](CROSS_DATASET.md). The 27 columns shared by
all three files are the `*_illuminating` content-classifier flags, so the
cross-platform story is about *what the content was about*:

- **Economy** is the top topic on every platform but peaks on **Twitter (~16%)**
  vs ads (~12%) vs FB posts (~9%).
- **Paid ads emphasize health (~11%) and women's issues (~8%)** far more than
  organic posts or tweets (~2–5%) — money buys attention for issues that don't
  trend organically.
- **Attack messaging** is highest on Twitter (~31%), lowest on FB posts (~22%);
  **advocacy** is near-constant (~55%) everywhere.
- The comparison also **auto-detected an integration bug**: an election-integrity
  flag is missing from the shared set only because of a malformed header in the
  posts file.

Reflections on generalization, code reuse, and how the three tools compare after
three tasks are in [`REFLECTION.md`](REFLECTION.md).

## Reproducibility

- Input files are CLI arguments; nothing is hardcoded.
- `pure_python_stats.py` and `cross_dataset.py` have **zero** dependencies.
- Verified three-way agreement on the ads file: 33 numeric columns, exact count
  match, max abs diff ~7e-08. Sample std (n-1), shared null tokens, one shared
  numeric rule.
