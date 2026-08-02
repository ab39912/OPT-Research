# Findings

## What this dataset is

This is a census of Facebook advertising in the 2024 U.S. Presidential race,
narrowed to ads that name at least one presidential candidate. There are 246,745
ads, and every `ad_id` is unique, so each row is one distinct ad purchase. The
ads were placed by 4,546 distinct pages. Although a handful of ads carry stray
foreign currencies (a few dozen in INR, GBP, EUR, and PKR), the dataset is
overwhelmingly a U.S. dollar story: 246,599 of the ads are in USD.

The first thing worth saying is what the data is *not*. Three of the columns you
would most want to treat as numbers, `spend`, `impressions`, and
`estimated_audience_size`, are not numbers. Facebook publishes these as bounded
ranges, stored here as dict-like strings such as
`{'lower_bound': '200', 'upper_bound': '299'}`. This is a real and consequential
data-quality feature, not a parsing nuisance: the platform deliberately reports
spend and reach in buckets, so no exact per-ad dollar figure exists in this data
at all. Every dollar figure below is therefore an estimate built by collapsing
each range to its midpoint and summing. That is a modeling choice, and it should
be read as "roughly," never as "exactly."

## Money is concentrated at the very top

If you sum the midpoint spend estimates, the total across the whole dataset is
on the order of **$262 million**. What is striking is how little of that is
spread out. The single biggest-spending page, the Kamala Harris campaign page,
accounts for an estimated **$83 million** on its own, roughly a third of the
entire total. Add the next few pages, Joe Biden (~$26M), Donald J. Trump
(~$20M), Kamala HQ (~$8M), and Tim Walz (~$7.6M), and a very small number of
official campaign entities account for the majority of all spending. Beyond
those, spend falls off quickly into a long tail of PACs, media pages, and small
organizations.

The per-ad distribution tells the same story from the other direction. The
median ad has an estimated spend around **$50**, the bottom bucket, while the
mean is over **$1,000** and the maximum single-ad estimate approaches **half a
million dollars**. That gap between a ~$50 median and a four-figure mean is the
signature of a heavily right-skewed distribution: a vast number of tiny ads, and
a small number of enormous ones doing most of the financial work. The spend
histogram (log-scaled, because a linear axis is unreadable here) makes the skew
visible at a glance.

## Spending is a countdown to Election Day

Grouping ads by creation month in 2024 shows an unmistakable ramp. The first few
months of the year sit around $6 million monthly. Spending roughly doubles into
early summer, then accelerates hard: about $31M in July, $35M in August, $45M in
September, and roughly **$85M in October** alone, the final full month before the
November 5 election. November itself is essentially empty, which makes sense: the
race was decided in its first week and new ad creation collapsed. The shape is
exactly what you would predict from campaign logic, money is held and then
spent in a crescendo at the moment it matters most, and it is reassuring to see
the data confirm it so cleanly.

## Trump dominates the conversation, even in others' ads

Candidate mentions are stored per-ad as a list. Counting across all ads, the
most-mentioned figure is **Donald Trump**, named in about 78,000 ads (with
"President Trump" appearing in a further ~22,000). **Kamala Harris** is next at
roughly 53,000, followed by **Joe Biden** (~24,000). Running mates and primary
challengers, JD Vance, Tim Walz, Nikki Haley, Ron DeSantis, trail well behind.

The interesting wrinkle is that mention counts and spending do not line up. The
Harris page is the top *spender* by a wide margin, yet Trump is the top *mention*
by an even wider one. That divergence is a hint that a large volume of ads name
Trump without being purchased by his campaign, opposition ads, issue ads, and
media pages invoking him as a subject. Mentions measure attention; spend
measures who is paying for it, and here the two point in different directions.

## What the ads are about

The dataset ships with automated content flags (the `illuminating_*` columns),
each a 0/1 indicator. Reading their means as prevalence rates: the most common
issue topics are the **economy** (~12% of ads), **health** (~11%), and
**social and cultural issues** (~11%), followed by **women's issues** (~8%).
At the other end, technology/privacy, military, and LGBTQ issues each appear in
well under 1% of ads. On message style, a slim majority of ads are flagged as
advocacy, and a notable **19%** are flagged for incivility, a meaningful share
if the classifier is trusted, and a good example of a number that invites a
follow-up question rather than settling one.

Nearly all ads run on the Facebook + Instagram combination (about 214,000 of
them); Facebook-only and Instagram-only are the next largest groups. The Meta
family is effectively the whole story; the standalone Audience Network and
Messenger placements are rounding error.

## What surprised me

Two things. First, how much of the analytical challenge here is *not* statistics
but data modeling, the headline economic variables do not exist as numbers and
have to be reconstructed, which quietly shapes every dollar figure anyone quotes
from this data. Second, the mention-versus-spend divergence: the candidate the
ads talk about most is not the candidate whose side is paying the most. That is
the kind of finding descriptive statistics are for, it does not prove anything
on its own, but it points a clear finger at the next question worth asking.
