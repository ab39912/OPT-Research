# Reflection — Milestone B

Responses to the milestone's research questions.

## How much Milestone A code was reusable? What broke?

Almost all of it. The three per-dataset scripts moved from Milestone A to
Milestone B essentially unchanged — the only edits were cosmetic (retitling, and
making the input path a required argument instead of defaulting to the ads file).
Nothing in the analysis logic broke, for one reason: Milestone A was already
written against dynamic type detection and a filename argument rather than a
fixed schema. The `datakit` module never mentions a specific column by name for
its *statistics*; it classifies whatever columns exist.

The one place Milestone A had a dataset-specific assumption was the **default
grouping keys** (`page_id`, `page_id`+`ad_id`), which are meaningful for ads but
not necessarily for posts or tweets. That is exactly the assumption Milestone B
is designed to expose, and it is handled by `datakit.suggest_group_keys`, which
picks keys from a preference list based on what the file actually contains and
falls back to any `*_id` column. So the "break" was anticipated and absorbed by
the shared layer rather than by editing each script.

If I had written Milestone A the tempting way — hardcoding column names, letting
each library infer its own dtypes, computing spend by referencing `spend`
directly — none of it would have survived contact with a second schema. The
lesson the milestone is teaching (plan the general design early) showed up
concretely: the up-front cost of the shared module is what made the reuse free.

## What made the code dataset-agnostic?

Four deliberate choices, all concentrated in `datakit`:

1. **Values decide types, not column names.** Classification reads the data, so
   an unknown file's columns are typed correctly without a schema.
2. **One numeric rule for all libraries.** Reading everything as strings and
   asking the shared classifier removes each library's inference from the
   picture, which is both what makes them agree *and* what makes them behave
   predictably on new files.
3. **Complex-value detection is generic.** "Looks like a range dict" and "looks
   like a list" are pattern checks, not `if col == 'spend'`. Any range column on
   any platform gets a midpoint companion automatically.
4. **Grouping is inferred, not assumed.** Keys come from what exists.

The net effect is that the only thing a new file needs is a path.

## Did the platforms tell the same story on shared columns?

Partly the same, partly not — and the *shared* columns turned out to be the
content-classifier flags rather than the engagement metrics, which shaped the
whole comparison. Only 27 columns are common to all three files, and every one
is an `*_illuminating` flag (message type, CTA, topic, incivility, scam, fraud).
None of the platform-native metrics (ad spend, Facebook likes, Twitter retweets)
is shared, because each platform measures engagement its own way. So the honest
cross-platform question this data can answer is "what was the political content
about?", not "where did it get the most engagement?"

On that question the platforms mostly rhyme but differ at the edges. **Advocacy
messaging is almost identical everywhere (~55%)**, which is a striking constant.
But **the economy leads as a topic everywhere yet peaks on Twitter (~16%)** vs
ads (~12%) vs Facebook posts (~9%); **attack messaging is highest on Twitter
(~31%) and lowest on FB posts (~22%)**; and, most interestingly, **paid ads
emphasize health (~11%) and women's issues (~8%) far more than organic posts or
tweets (~2–5%)**. That last gap is the kind of finding descriptive statistics are
for: campaigns evidently *pay* to raise issues that don't surface as strongly in
organic feeds.

Where I *did* get to compare engagement — within each file separately — the
structural expectation held emphatically: every engagement metric is severely
right-skewed, and Twitter is the most extreme (view counts with a median around
71k but a max of 333 million). Comparing medians rather than means is not
optional there; the mean is a fiction dragged up by a few viral outliers.

A second, more mundane finding the comparison produced on its own: **fewer
columns are truly shared than the schemas suggest, and one was lost to a
malformed header.** `election_integrity_Truth_illuminating` exists in all three
conceptually, but in the posts file it is fused to the previous column, so the
mechanical intersection drops it. That is a data-integration finding, not a
political one, and the cross-dataset tool surfaced it without anyone looking —
which is precisely why running the mechanical check is worth it.

## What would a colleague need to change for a totally different dataset?

For a public-health survey or a financial-transaction log, **most of it would
just work**: loading, type detection, missing-value handling, per-column stats,
and the cross-file comparison are all schema-independent. Two things would need
attention. First, **grouping keys** — `suggest_group_keys` prefers social-media
identifiers, so a colleague would either pass `--group-by` explicitly or extend
the preference list (a one-line change) for their domain's natural keys
(`patient_id`, `account_number`). Second, **domain-specific cleaning** — this
system knows about Facebook range dicts and list-strings; a new domain with its
own encoded columns (say, currency strings like `"$1,234.56"` or ISO durations)
would want a new transform registered in `datakit.TRANSFORMS` and a matching
detector. That extension point is deliberately small and centralized: you add
one detector and one transform, and all three scripts pick it up.

## How has your view of pure Python vs. Pandas vs. Polars evolved?

Across three tasks my initial impressions mostly held but sharpened. Pure Python
went from "tedious" to "tedious but indispensable once, and genuinely portable
forever after" — the pure-Python and cross-dataset scripts have zero
dependencies, which is a real operational advantage for something you want a
colleague to run without setting up an environment. Pandas stayed the default
for exploratory work but I trust its *silent* behavior less than I did — the
whole reason the three agree is that I took the type/null decisions away from it.
Polars impressed me more with repeated use: strict typing turned several latent
bugs into loud errors at the boundary, and its expression API made the grouped
aggregations the most readable of the three. If I were starting the system fresh
today I'd still prototype in Pandas but would seriously consider Polars as the
production engine for anything load-heavy.

## Can AI tools handle the *generalization* problem?

Less well than the single-file problem, in a telling way. Asked to "write
descriptive stats for this CSV," AI tools produce competent, idiomatic,
*dataset-specific* code — they will reference `spend` and `page_id` by name and
lean on each library's dtype inference. Asked explicitly to "make it work on any
schema," they improve, but their instinct is still to solve the example in front
of them rather than to build the shared decision layer that keeps multiple
implementations consistent. The cross-implementation agreement requirement in
particular is something they rarely design for unprompted, because it is a
*systems* constraint, not a local coding task. My takeaway across the three
tasks: these tools are excellent accelerators for the parts I can specify
precisely, and they are no substitute for owning the small set of decisions
(types, nulls, cleaning, grouping) that determine whether the whole system is
correct and general. That division of labor — let the tool draft, keep the
judgment centralized and under my control — is the most durable thing I'm taking
from this sequence.
