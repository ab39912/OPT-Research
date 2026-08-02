# Reflection — Milestone A

Responses to the milestone's research questions, based on building all three
implementations against a Facebook-ads dataset of this structure.

## Was it hard to make the three agree? What caused discrepancies?

The statistics themselves are trivial; making three libraries agree on them is
where the real work is, and almost all of it is about *type and null decisions*,
not arithmetic. Three specific things had to be pinned down:

1. **Standard deviation convention.** Pandas and Polars both default to the
   sample std (ddof=1); a naive hand-rolled version divides by `n`. Left
   unaligned, every std silently disagrees. The pure-Python code divides by
   `n−1` on purpose.

2. **Who decides what is numeric.** If you let each library infer dtypes on
   load, they will disagree at the edges — a column that is all `"0"`/`"1"`
   except for one `""` might be float in one library and object in another, and
   the range-dict columns get read as strings by everyone but for different
   reasons. I removed the library from that decision entirely: every script
   reads all columns as strings and asks the shared `datakit.classify_column`
   whether a column is numeric, using one all-or-nothing rule. Agreement then
   holds by construction rather than by luck.

3. **Null tokens.** `""`, `"NA"`, `"None"`, etc. must map to null identically.
   Pandas takes an `na_values` list, Polars takes `null_values`, and pure Python
   checks a set — all three point at the same token list.

After those three, the residual difference across 31 numeric columns was ~1.4e-08
(floating-point noise), with exact agreement on counts. That is the standard I'd
want before trusting any of the numbers.

## Do you find one approach easier or more performant?

**Developer experience.** Pandas is the easiest to *start* with — `read_csv`,
`describe`, `groupby` are muscle memory and the docs/examples are everywhere.
Polars is the most pleasant to *read* once written: the expression API
(`df.group_by(keys).agg([pl.len(), pl.col(m).mean()])`) states intent directly,
and strict typing meant several of my sloppy assumptions failed loudly at the
boundary instead of silently producing a wrong number. Pure Python is the most
work by a wide margin — grouping is a hand-built `defaultdict(list)`, the median
needs an explicit even/odd split — but it is the only one where nothing is
hidden.

**Performance.** I benchmarked with `benchmark.py` (load + mean of every numeric
column). The headline is a caveat: on this ~113MB file, CSV *parsing* dominates,
so pure Python and Pandas landed close (~10s each) when both read the file as
strings. That is a genuinely useful lesson — the "Pandas is faster" intuition is
about vectorized computation, and if your workload is I/O- and parse-bound, the
computation speedup barely shows. Polars typically wins this kind of load-heavy
job thanks to its multithreaded Rust CSV reader, and its lazy API (`scan_csv`
+ predicate/projection pushdown) would widen the gap further by not
materializing columns it does not need — but I could not benchmark Polars in my
sandbox (no install), so I am reporting the expectation, not a measurement.

## Which approach would you tell a junior analyst to learn first?

**Pandas first**, then Polars, with a *single* pure-Python exercise early on.
Pandas is the lingua franca: the ecosystem, tutorials, Stack Overflow answers,
and most colleagues' code are Pandas, so it maximizes their ability to be useful
and to read others' work. But I would have them write the pure-Python version
*once* on an unfamiliar file, precisely because it refuses to hide the decisions
(nulls, type coercion, aggregation semantics) that Pandas makes silently — you
cannot write it without understanding your data. Polars comes third, as the
"when you care about performance or want stricter, more predictable semantics"
upgrade, once they already have a mental model to map onto its expressions.

## Can AI coding tools jumpstart each approach? Do you agree with their defaults?

Yes for scaffolding, with supervision. Asked for "descriptive statistics in
Pandas," these tools reliably produce `df.describe()` plus `value_counts()` and
`isna().sum()`, which is a fine starting point. Where their defaults fall short
is exactly the part that matters here:

- They tend to **trust the library's dtype inference** and won't, unprompted,
  notice that `spend` is a range dict rather than a number. On this dataset that
  silently drops the most important variable from the numeric summary.
- They default to **each library's native describe**, which means the Pandas and
  Polars versions won't necessarily agree on nulls or on which columns count as
  numeric — the very problem this milestone is about.
- For std they usually inherit the library default (sample std), which happens to
  be right, but they rarely *say* so, so you can't tell whether agreement is
  intentional.

So they are good for boilerplate and bad at the cross-implementation
consistency and data-cleaning judgment that make the results trustworthy. I used
that division of labor here: let them (and myself) scaffold the obvious calls,
then hand the type/null/cleaning decisions to one shared module I control.

## What cleaning did the complex columns require, and did the tools differ?

This file has four columns that can't be summarized as-is, and — usefully — they
are not all the same *kind* of complex, which is exactly why detection has to be
value-based rather than name-based:

- **Two list columns** (`publisher_platforms` like `['facebook','instagram']`,
  `illuminating_mentions` like `['Kamala Harris','Tim Walz']`) get element-count
  companions (`*__n_items`), derived identically in all three scripts.
- **Two nested-dict columns** (`delivery_by_region`,
  `demographic_distribution`, e.g. `{'Texas': {'spend': 249, 'impressions':
  47499}}`) are recognized as complex and reported as categorical. I chose *not*
  to auto-explode them into per-region/per-demographic numeric columns: that is a
  real analysis in its own right, and forcing it into the generic summary would
  produce a misleading flat table. Detecting them and leaving them labeled is the
  honest move.

A notable contrast with Task 1: there, `spend`/`impressions` were range dicts
(`{'lower_bound':…}`) that *had* to be reconstructed to midpoints before any
dollar figure existed. **On this file `estimated_spend` is already a plain
integer**, so the numeric summary is exact rather than an estimate. The same
`datakit` classifier handles both cases without special-casing — the range-dict
→ midpoint path simply doesn't fire here — which is the whole point of putting
detection in one value-driven place.

Where the libraries differed was in *applying* a transform, not deciding it.
Pandas uses `.map`, Polars uses `.map_elements` with an explicit `return_dtype`
(its strictness surfacing again), and pure Python is a list comprehension.
Polars' insistence on a declared return type is a small friction that pays off:
it turns a silently all-null column into an immediate, fixable error.
