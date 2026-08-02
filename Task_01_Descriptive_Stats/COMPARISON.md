# Comparison: pure Python vs. pandas

## Do the results agree?

Yes, for every genuinely numeric column, and to the precision displayed. The 26
`illuminating_*` indicator columns produce identical count, mean, min, max,
standard deviation, and median in both scripts. For example, both report
`illuminating_scam` with mean 0.0716 and std 0.2579, and
`illuminating_topic_economy` with mean 0.1221 and std 0.3274.

They agree because I made two deliberate choices to force agreement:

1. **Same standard deviation convention.** Both use the *sample* standard
   deviation with an n−1 denominator. Pandas defaults to this (`ddof=1`); the
   pure-Python `compute_numeric_stats` divides by `count - 1` for the same
   reason. Had the manual version divided by `n`, every std would have been
   slightly smaller and the scripts would silently disagree, a classic and
   easy-to-miss bug.
2. **Same missing-value tokens.** Both treat `""`, `NA`, `N/A`, `nan`, `None`,
   and `null` as missing. In pandas this is the `na_values` argument on
   `read_csv`; in pure Python it is the `MISSING_TOKENS` set checked by
   `is_missing`.

## Where did pure Python force decisions that pandas made silently?

This is the heart of the exercise. Pandas quietly made at least four decisions
that the manual version had to make out loud:

**1. What counts as a number.** Pandas ran type inference on load and decided
the `illuminating_*` columns were integers and everything else was `object`.
The pure-Python script had to implement that judgment by hand in `infer_type`,
using an all-or-nothing rule: a column is numeric only if *every* non-missing
value parses. Writing that rule is what surfaces the key fact that `spend`,
`impressions`, and `estimated_audience_size` are **not** numeric, they are
dict-like strings. Pandas reached the same conclusion, but it never made me look
at it. The manual version made the data-quality issue impossible to ignore.

**2. What counts as missing.** Pandas has a built-in notion of `NaN` and a
default `na_values` list. The manual version has no such notion; a missing cell
is just an empty string until you decide otherwise. I had to author the missing
policy explicitly, which meant I actually understood it.

**3. How to break ties in the mode.** When several values share the top
frequency, `collections.Counter.most_common` and pandas `value_counts` can order
ties differently. For a "most frequent value" this rarely changes the headline,
but it is a silent divergence that only becomes visible once you have written
the manual path.

**4. Memory and iteration strategy.** Pandas loaded all 40 columns into typed
arrays without my thinking about it. In pure Python I had to decide to build a
column-major view in a single pass over the rows, because the naive approach
(re-scanning every row for every column) would be far slower on 247k rows. That
cost is hidden entirely behind `DataFrame.describe()`.

## What did writing the pure-Python version teach me?

The biggest lesson was about the three range-encoded columns. If I had opened
only pandas, run `df.describe()`, and seen `spend` land in the object/categorical
section, I might have shrugged and moved on. Writing `infer_type` forced me to
articulate *why* it is not numeric, and that led directly to the most important
modeling decision in the whole project: that any dollar figure has to be
reconstructed from range midpoints and is therefore an estimate, not a fact.
That single realization reshapes how every number in `FINDINGS.md` should be
read.

The second lesson was humility about "free" statistics. `describe()` gives you
count, mean, std, quartiles, min, and max in one call, and it is genuinely
excellent. But having built the mean, std, and median by hand, including the
even/odd median split and the n−1 std, I now know exactly what those numbers
mean and where they can mislead (for instance, that the mean spend is dragged
far above the median by a few giant ads). The manual version is slower to write
and slower to run, and I would never ship it to production. But it is the reason
I trust the pandas output rather than merely accepting it.

## Practical takeaway

Use pandas for the work. Write the manual version once, early, on an unfamiliar
dataset, precisely because it refuses to hide the decisions that pandas makes for
you. The value is not the code; it is that you cannot write it without
understanding your data.
