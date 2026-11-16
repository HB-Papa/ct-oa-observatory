"""Known-answer tests for pipeline/metrics.py. Each fixture is small enough to
check by hand; the expected numbers are worked out in the comments."""
import pandas as pd
import pytest

from pipeline import metrics as m

# Four works. W1 Yale+UConn collaboration, W2 Yale only, W3 UConn only, W4 Wesleyan only.
WORKS = pd.DataFrame([
    # work_id, year, oa_category, apc_list_usd, n_corresponding_institutions, field, publisher
    ("W1", 2020, "gold",   3000.0, 2, "Medicine", "Pub A"),
    ("W2", 2020, "closed", None,   1, "Medicine", "Pub B"),
    ("W3", 2021, "hybrid", 5000.0, 1, "Physics",  "Pub A"),
    ("W4", 2026, "hybrid", None,   0, None,       "Pub B"),
], columns=["work_id", "publication_year", "oa_category", "apc_list_usd",
            "n_corresponding_institutions", "field_name", "publisher_parent_name"])

WI = pd.DataFrame([
    # W1: both Yale and UConn are corresponding (2 corresponding institutions)
    ("W1", "yale", True), ("W1", "uconn", True),
    ("W2", "yale", True),
    ("W3", "uconn", False),   # UConn author, but corresponding author is elsewhere
    ("W4", "wesleyan", False),
], columns=["work_id", "institution_key", "is_corresponding_institution"])


def test_period_labels():
    assert m.period(2015) == "complete" and m.period(2025) == "complete"
    assert m.period(2026) == "incomplete"


def test_institution_works_counts_collaboration_for_each_institution():
    iw = m.institution_works(WORKS, WI)
    assert iw.groupby("institution_key").size().to_dict() == {"uconn": 2, "wesleyan": 1, "yale": 2}


def test_statewide_counts_each_work_once():
    sw = m.statewide_works(WORKS, WI)
    assert sorted(sw.work_id) == ["W1", "W2", "W3", "W4"]  # 4, not 5 institution rows


def test_statewide_without_yale_keeps_shared_work_drops_yale_only():
    sw = m.statewide_works(WORKS, WI, exclude=("yale",), label="statewide_no_yale")
    assert sorted(sw.work_id) == ["W1", "W3", "W4"]  # W2 is Yale-only
    assert set(sw.institution_key) == {"statewide_no_yale"}


def test_oa_breakdown_fills_zeros_and_shares_sum_to_one():
    iw = m.institution_works(WORKS, WI)
    out = m.oa_breakdown(iw, ["institution_key"])
    yale = out[out.institution_key == "yale"].set_index("oa_category")
    assert len(yale) == 7                                   # every category present
    assert yale.loc["gold", "works"] == 1 and yale.loc["closed", "works"] == 1
    assert yale.loc["green", "works"] == 0
    assert yale.loc["gold", "share"] == pytest.approx(0.5)
    assert out.groupby("institution_key")["share"].sum().round(10).eq(1).all()


def test_free_to_read_summary():
    out = m.free_to_read_summary(m.institution_works(WORKS, WI), ["institution_key"]).set_index("institution_key")
    assert out.loc["yale", "works"] == 2 and out.loc["yale", "free_to_read"] == 1   # W1 gold, W2 closed
    assert out.loc["uconn", "free_to_read_share"] == 1.0                             # W1 gold, W3 hybrid


def test_top_groups_unknown_label_and_closed_counts():
    out = m.top_groups(m.statewide_works(WORKS, WI), ["institution_key"], "field_name", n=5)
    rows = out.set_index("field_name")
    assert rows.loc["Medicine", "works"] == 2 and rows.loc["Medicine", "closed"] == 1
    assert rows.loc["Unknown", "works"] == 1                 # W4 has no field, kept as Unknown
    assert rows.loc["Medicine", "rank_by_output"] == 1


def test_apc_upper_bound_credits_every_institution_full_fee():
    iw = m.institution_works(WORKS, WI)
    out = m.apc_estimate(iw, ["institution_key"], corresponding_only=False).set_index("institution_key")
    # Yale: W1 gold $3000 (W2 closed, not counted). UConn: W1 $3000 + W3 hybrid $5000.
    assert out.loc["yale", "estimated_usd"] == 3000
    assert out.loc["uconn", "estimated_usd"] == 8000
    # Wesleyan: W4 is hybrid but has no list price -> $0 known, 1 work without price.
    assert out.loc["wesleyan", "estimated_usd"] == 0
    assert out.loc["wesleyan", "works_without_list_price"] == 1


def test_apc_corresponding_only():
    iw = m.institution_works(WORKS, WI)
    out = m.apc_estimate(iw, ["institution_key"], corresponding_only=True).set_index("institution_key")
    # W1 has two corresponding institutions: each is credited the full $3000.
    assert out.loc["yale", "estimated_usd"] == 3000
    assert out.loc["uconn", "estimated_usd"] == 3000         # W3 drops out: UConn not corresponding
    assert "wesleyan" not in out.index


def test_apc_statewide_counts_each_fee_once():
    sw = m.statewide_works(WORKS, WI)
    any_corr = WI.groupby("work_id")["is_corresponding_institution"].any()
    sw["is_corresponding_institution"] = sw.work_id.map(any_corr)
    upper = m.apc_estimate(sw, ["institution_key"], corresponding_only=False).iloc[0]
    corr = m.apc_estimate(sw, ["institution_key"], corresponding_only=True).iloc[0]
    assert upper.estimated_usd == 8000     # W1 3000 + W3 5000, W1 not doubled
    assert corr.estimated_usd == 3000      # only W1 has a CT corresponding institution


def test_corresponding_coverage():
    out = m.corresponding_coverage(m.statewide_works(WORKS, WI), ["institution_key"]).iloc[0]
    assert out.works == 4 and out.with_corresponding_info == 3   # W4 has none
    assert out.coverage_share == pytest.approx(0.75)


def test_apc_statewide_without_yale_ignores_yale_corresponding():
    # W5: Yale + Wesleyan, gold $2000, only Yale is corresponding.
    works = pd.concat([WORKS, pd.DataFrame([("W5", 2020, "gold", 2000.0, 1, "Medicine", "Pub A")],
                                           columns=WORKS.columns)], ignore_index=True)
    wi = pd.concat([WI, pd.DataFrame([("W5", "yale", True), ("W5", "wesleyan", False)],
                                     columns=WI.columns)], ignore_index=True)
    swn = m.statewide_works(works, wi, exclude=("yale",), label="statewide_no_yale")
    swn["is_corresponding_institution"] = swn.work_id.map(m.any_corresponding(wi, exclude=("yale",)))
    out = m.apc_estimate(swn, ["institution_key"], corresponding_only=True).iloc[0]
    # W1 ($3000, UConn corresponding) counts. W5 is in the set (Wesleyan author) but
    # only Yale is corresponding, so its $2000 is not counted.
    assert out.estimated_usd == 3000
    up = m.apc_estimate(swn, ["institution_key"], corresponding_only=False).iloc[0]
    assert up.estimated_usd == 3000 + 5000 + 2000   # upper bound: W1, W3, W5


def test_fee_unconfirmed_counts_as_free_to_read_and_not_paid():
    works = pd.DataFrame([("A", 2020, "oa_fee_unconfirmed", None, 1, "X", "P"),
                          ("B", 2020, "closed", None, 1, "X", "P")], columns=WORKS.columns)
    wi = pd.DataFrame([("A", "yale", True), ("B", "yale", True)], columns=WI.columns)
    iw = m.institution_works(works, wi)
    s = m.free_to_read_summary(iw, ["institution_key"]).iloc[0]
    assert s.free_to_read == 1 and s.works == 2
    assert m.apc_estimate(iw, ["institution_key"], corresponding_only=False).empty
