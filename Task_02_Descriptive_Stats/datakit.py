#!/usr/bin/env python3
"""
datakit.py  -- shared, standard-library-only helpers.

This module is the "system" layer that all three scripts (pure Python, Pandas,
Polars) agree to obey. It contains ZERO third-party imports so that it can be
used by the pure-Python script without violating the "standard library only"
rule, while the Pandas and Polars scripts import the SAME detection logic so
that all three make identical decisions about:

  * what counts as missing
  * what counts as numeric (an all-or-nothing rule, not per-library inference)
  * which columns are "complex" (Facebook range dicts, list-strings) and how to
    derive clean numeric companions from them

Making the three libraries agree is the graded crux of this task. They agree
because they share this file, not by coincidence.
"""

import ast
import re

# Cells equal to one of these (case-insensitive, stripped) are treated as null.
MISSING_TOKENS = {"", "na", "n/a", "nan", "none", "null"}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


# --------------------------------------------------------------------------- #
# Missing / primitive type tests
# --------------------------------------------------------------------------- #
def is_missing(value):
    return value is None or str(value).strip().lower() in MISSING_TOKENS


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
    v = str(value).strip()
    if not _DATE_RE.match(v):
        return False
    y, m, d = v[:10].split("-")
    return 1 <= int(m) <= 12 and 1 <= int(d) <= 31


# --------------------------------------------------------------------------- #
# Complex-value detection + cleaning
# --------------------------------------------------------------------------- #
def is_range_dict(value):
    """True for Facebook range strings like {'lower_bound':'200','upper_bound':'299'}."""
    v = str(value).strip()
    return v.startswith("{") and "lower_bound" in v


def parse_range_midpoint(value):
    """Collapse a range dict string to the midpoint of its bounds (float) or None."""
    try:
        d = ast.literal_eval(str(value))
        lo, up = d.get("lower_bound"), d.get("upper_bound")
        lo = float(lo) if lo not in (None, "") else None
        up = float(up) if up not in (None, "") else lo
        if lo is None:
            return None
        return (lo + up) / 2 if up is not None else lo
    except (ValueError, SyntaxError, AttributeError, TypeError):
        return None


def is_list_string(value):
    """True for list-encoded strings like ['facebook','instagram']."""
    v = str(value).strip()
    return v.startswith("[") and v.endswith("]")


def parse_list_length(value):
    """Number of elements in a list-string, or None if unparseable."""
    try:
        parsed = ast.literal_eval(str(value))
        return len(parsed) if isinstance(parsed, (list, tuple)) else None
    except (ValueError, SyntaxError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Column classification (from a sample of raw string values)
# --------------------------------------------------------------------------- #
def classify_column(values):
    """Return the apparent kind of a column given its raw string values.

    One of: 'empty', 'integer', 'float', 'date', 'range', 'list', 'string'.
    Numeric verdicts are all-or-nothing: EVERY non-missing value must qualify.
    """
    non_missing = [v for v in values if not is_missing(v)]
    if not non_missing:
        return "empty"
    if all(try_int(v) for v in non_missing):
        return "integer"
    if all(try_float(v) for v in non_missing):
        return "float"
    # Complex kinds are recognized if a clear majority match, since real files
    # mix in the occasional blank or malformed cell.
    if _fraction(non_missing, is_range_dict) >= 0.9:
        return "range"
    if _fraction(non_missing, is_list_string) >= 0.9:
        return "list"
    if all(looks_like_date(v) for v in non_missing):
        return "date"
    return "string"


def _fraction(values, predicate):
    if not values:
        return 0.0
    return sum(1 for v in values if predicate(v)) / len(values)


def derived_columns(kinds):
    """Given {col: kind}, return the derived clean columns to create.

    Returns a dict: new_col_name -> (source_col, transform_name).
    'range'  -> <col>__midpoint  (numeric midpoint of the bounds)
    'list'   -> <col>__n_items   (element count)
    These derived columns are what make spend/impression analysis meaningful,
    and every script derives them identically.
    """
    derived = {}
    for col, kind in kinds.items():
        if kind == "range":
            derived[f"{col}__midpoint"] = (col, "range_midpoint")
        elif kind == "list":
            derived[f"{col}__n_items"] = (col, "list_length")
    return derived


TRANSFORMS = {
    "range_midpoint": parse_range_midpoint,
    "list_length": parse_list_length,
}


# --------------------------------------------------------------------------- #
# Group-key suggestion (used by the generalized Milestone-B system)
# --------------------------------------------------------------------------- #
# "Owner" hints identify the account/author/page that produced a record — the
# closest analog to the ads' page_id, and usually the most useful grouping.
# Kept specific on purpose: a bare "page" would wrongly match "Page Category".
_OWNER_HINTS = ("facebook_id", "account", "author", "sponsor_id", "from_id",
                "user_id", "handle", "channel", "page_id", "page_name")
# "Dimension" hints identify categorical facets worth grouping by.
_DIM_HINTS = ("source", "lang", "type", "category", "country", "month",
              "year", "region", "currency", "platform", "party", "candidate",
              "state", "gender")


def _uniques(values):
    return {str(v).strip() for v in values if not is_missing(v)}


def choose_group_keys(header, sample):
    """Pick sensible grouping keys for an *unknown* schema, using a data sample.

    `sample` maps each column name to a list of that column's raw string values
    (a few thousand rows is plenty). Returns a list of key-lists to group by.

    Strategy, in order:
      1. If `page_id` exists, always emit [page_id] and — when `ad_id` also
         exists — [page_id, ad_id]. This satisfies the ads requirement exactly,
         including the deliberately near-degenerate page_id+ad_id grouping.
      2. Otherwise, rank columns from the sample and return up to two useful
         single-key groupings: the best "owner" identifier (an account/author
         that repeats) plus the best categorical "dimension". Columns that are
         constant, effectively unique-per-row, complex (dict/list), dates, or
         empty are skipped, so we never pick a useless key like a tweet id.
    """
    hdr = set(header)
    if "page_id" in hdr:
        groupings = [["page_id"]]
        if "ad_id" in hdr:
            groupings.append(["page_id", "ad_id"])
        return groupings

    n = max((len(v) for v in sample.values()), default=1)
    owners, dims, others = [], [], []
    for col in header:
        vals = sample.get(col, [])
        kind = classify_column(vals)
        if kind in ("empty", "range", "list", "date", "float"):
            continue  # skip complex/continuous/date/empty as grouping keys
        uniq = _uniques(vals)
        u = len(uniq)
        present = sum(1 for v in vals if not is_missing(v)) or 1
        ratio = u / present
        if u < 2 or ratio > 0.6:
            continue  # skip constant and near-unique-per-row columns
        if uniq <= {"0", "1"}:
            continue  # skip binary indicator flags (e.g. the *_illuminating 0/1)
        name = col.lower()
        entry = (u, col)
        if any(h in name for h in _OWNER_HINTS):
            owners.append(entry)   # owners may be low-cardinality identifiers
        elif u >= 3 and any(h in name for h in _DIM_HINTS):
            dims.append(entry)     # dimensions need 3+ distinct values
        elif u >= 3:
            others.append(entry)

    owners.sort()
    dims.sort()
    others.sort()

    groupings = []
    if owners:
        groupings.append([owners[0][1]])
    # Add the best dimension (prefer named dimensions, then anything usable).
    dim_pool = dims or others
    if dim_pool:
        pick = dim_pool[0][1]
        if [pick] not in groupings:
            groupings.append([pick])
    # If we still have nothing (or only one) and there are leftovers, top up.
    for pool in (owners, dims, others):
        for _, col in pool:
            if len(groupings) >= 2:
                break
            if [col] not in groupings:
                groupings.append([col])
    if not groupings and header:
        groupings.append([header[0]])
    return groupings


def suggest_group_keys(header):
    """Header-only fallback kept for backward compatibility. Prefer
    choose_group_keys(header, sample), which is data-aware."""
    hdr = set(header)
    if "page_id" in hdr:
        return ([["page_id"], ["page_id", "ad_id"]] if "ad_id" in hdr
                else [["page_id"]])
    id_cols = [c for c in header if c.lower().endswith("_id")]
    return [[id_cols[0]]] if id_cols else ([[header[0]]] if header else [])
