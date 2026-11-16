"""Metric definitions. Every number on the site comes from one of these functions.

Each function takes plain tables (pandas DataFrames) and returns a table, with
no API calls or file access, so each one can be tested with a tiny hand-made
example whose right answer is known (tests/test_metrics.py).

Inputs
- works: one row per work (from works.parquet), already filtered to in_scope.
         The OA column used is oa_category (OpenAlex oa_status with diamond split).
- wi:    one row per work x institution (from work_institutions.parquet),
         columns work_id, institution_key, is_corresponding_institution.
"""
from __future__ import annotations

import pandas as pd

# OA categories reported on the site. OpenAlex's statuses, with "diamond" split
# into fee-confirmed diamond and "oa_fee_unconfirmed" (see s04 oa_category).
OA_CATEGORIES = ["diamond", "oa_fee_unconfirmed", "gold", "hybrid", "bronze", "green", "closed"]
OA_STATUSES = OA_CATEGORIES  # older name, kept for readability in tests
FREE_TO_READ = ["diamond", "oa_fee_unconfirmed", "gold", "hybrid", "bronze", "green"]  # everything but closed
PAID_OA = ["gold", "hybrid"]  # statuses where an APC is normally charged
COMPLETE_YEARS = range(2015, 2026)
INCOMPLETE_YEARS = {2026}


def period(year: int) -> str:
    """2015-2025 are complete years. 2026 is shown separately, labeled incomplete."""
    return "incomplete" if year in INCOMPLETE_YEARS else "complete"


# ---------------------------------------------------------------- unit of count

def institution_works(works: pd.DataFrame, wi: pd.DataFrame) -> pd.DataFrame:
    """One row per (institution, work). A work counts for every institution with
    at least one author there, so a Yale-UConn paper appears once under each."""
    return wi[["work_id", "institution_key", "is_corresponding_institution"]].merge(
        works, on="work_id", how="inner")


def statewide_works(works: pd.DataFrame, wi: pd.DataFrame, exclude: tuple[str, ...] = (),
                    label: str = "statewide") -> pd.DataFrame:
    """Statewide set: each work once, however many Connecticut institutions share it.

    With exclude=("yale",), keeps works that have at least one author at an
    institution other than Yale. A Yale-only paper drops out; a Yale-UConn
    paper stays (UConn is on it)."""
    keep = wi.loc[~wi.institution_key.isin(exclude), "work_id"].unique()
    out = works[works.work_id.isin(keep)].copy()
    out["institution_key"] = label
    return out


def any_corresponding(wi: pd.DataFrame, exclude: tuple[str, ...] = ()) -> pd.Series:
    """Per work: True if any Connecticut institution (other than those excluded)
    is a corresponding institution. Used for statewide APC attribution, so the
    "without Yale" figure only credits works with a non-Yale corresponding
    institution."""
    d = wi[~wi.institution_key.isin(exclude)]
    out = d.groupby("work_id")["is_corresponding_institution"].any()
    return out.reindex(wi.work_id.unique(), fill_value=False)


# ---------------------------------------------------------------- question 1 & 2

def oa_breakdown(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Works and share by OA category within each group. Every category appears for
    every group, with 0 where there are none, so tables and charts line up."""
    counts = df.groupby(by + ["oa_category"]).size().rename("works").reset_index()
    groups = df[by].drop_duplicates()
    full = groups.merge(pd.DataFrame({"oa_category": OA_CATEGORIES}), how="cross")
    out = full.merge(counts, on=by + ["oa_category"], how="left").fillna({"works": 0})
    out["works"] = out["works"].astype(int)
    totals = out.groupby(by)["works"].transform("sum")
    out["share"] = out["works"] / totals
    out["oa_category"] = pd.Categorical(out["oa_category"], OA_CATEGORIES, ordered=True)
    return out.sort_values(by + ["oa_category"]).reset_index(drop=True)


def free_to_read_summary(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Total works, works free to read (any status but closed), and the share."""
    g = df.groupby(by)
    out = pd.DataFrame({
        "works": g.size(),
        "free_to_read": g["oa_category"].apply(lambda s: s.isin(FREE_TO_READ).sum()),
    }).reset_index()
    out["free_to_read_share"] = out["free_to_read"] / out["works"]
    return out


# ---------------------------------------------------------------- question 3

def top_groups(df: pd.DataFrame, by: list[str], dim: str, n: int = 10) -> pd.DataFrame:
    """For each group (e.g. institution), the top n values of `dim` (field, topic,
    publisher) by output, with how many of those works are closed.
    Missing values are labeled "Unknown" rather than dropped, so totals add up."""
    d = df.assign(**{dim: df[dim].fillna("Unknown")})
    g = d.groupby(by + [dim])
    out = pd.DataFrame({"works": g.size(),
                        "closed": g["oa_category"].apply(lambda s: (s == "closed").sum())}).reset_index()
    out["closed_share"] = out["closed"] / out["works"]
    out["rank_by_output"] = out.groupby(by)["works"].rank(method="first", ascending=False).astype(int)
    out["rank_by_closed"] = out.groupby(by)["closed"].rank(method="first", ascending=False).astype(int)
    keep = (out.rank_by_output <= n) | (out.rank_by_closed <= n)
    return out[keep].sort_values(by + ["rank_by_output"]).reset_index(drop=True)


# ---------------------------------------------------------------- question 4

def apc_estimate(df: pd.DataFrame, by: list[str], corresponding_only: bool) -> pd.DataFrame:
    """Estimated APC spending, from journal list prices (apc_list_usd). ESTIMATE.

    Only gold and hybrid works are counted: those are the statuses where an APC
    is normally charged. A price missing in OpenAlex counts as unknown, not $0,
    and the number of works without a price is reported.

    corresponding_only=False  Upper bound. Every institution with any author on
                              the work is credited the full list price.
    corresponding_only=True   More defensible. Only works where the institution
                              is a corresponding institution. When several
                              institutions are corresponding, each is credited
                              the full fee (stated on the Methods page).
    For statewide rows, pass a frame with one row per work (statewide_works) and
    a column is_corresponding_institution meaning "any CT institution is
    corresponding", so each work's fee is counted once."""
    d = df[df.oa_category.isin(PAID_OA)]
    if corresponding_only:
        d = d[d.is_corresponding_institution]
    g = d.groupby(by)
    out = pd.DataFrame({
        "paid_oa_works": g.size(),
        "works_with_list_price": g["apc_list_usd"].apply(lambda s: s.notna().sum()),
        "estimated_usd": g["apc_list_usd"].sum(min_count=0),
    }).reset_index()
    out["works_without_list_price"] = out.paid_oa_works - out.works_with_list_price
    out["method"] = "corresponding_author" if corresponding_only else "upper_bound_all_authors"
    return out


def corresponding_coverage(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """How many works have any corresponding institution recorded in OpenAlex.
    The defensible APC estimate can only see these works."""
    g = df.groupby(by)
    out = pd.DataFrame({"works": g.size(),
                        "with_corresponding_info": g["n_corresponding_institutions"].apply(lambda s: (s > 0).sum())
                        }).reset_index()
    out["coverage_share"] = out.with_corresponding_info / out.works
    return out
