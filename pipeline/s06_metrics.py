"""Step 3: compute every published metric from the tidy tables.

Reads data/derived/*.parquet (no API calls) and writes CSVs to
data/derived/metrics/. These CSVs are what the site displays and what the
Data Downloads page publishes. Definitions live in pipeline/metrics.py.

"entity" is an institution key, "statewide" (each work once), or
"statewide_no_yale" (each work once, works with at least one non-Yale
Connecticut author).
"""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from pipeline import metrics as m
from pipeline.config import DERIVED, snapshot
from pipeline.institutions import INSTITUTIONS, NAMES

OUT = DERIVED / "metrics"
WORK_COLS = ["work_id", "publication_year", "oa_category", "apc_list_usd", "n_corresponding_institutions",
             "field_name", "topic_name", "publisher_parent_name"]


def load():
    works = pd.read_parquet(DERIVED / "works.parquet")
    wi = pd.read_parquet(DERIVED / "work_institutions.parquet")
    works = works[works.in_scope][WORK_COLS]
    wi = wi[wi.in_scope]
    return works, wi


def entities(works, wi) -> pd.DataFrame:
    """Stack institution rows and the two statewide sets into one frame with an
    'entity' column. is_corresponding_institution for statewide rows means any
    Connecticut institution in that set is corresponding."""
    iw = m.institution_works(works, wi)
    sw = m.statewide_works(works, wi, label="statewide")
    swn = m.statewide_works(works, wi, exclude=("yale",), label="statewide_no_yale")
    sw["is_corresponding_institution"] = sw.work_id.map(m.any_corresponding(wi))
    # Without Yale: corresponding means a non-Yale CT institution is corresponding.
    # (Fixed 2026-11-16 after the verification agent found Yale-only corresponding
    # works counted in this figure.)
    swn["is_corresponding_institution"] = swn.work_id.map(m.any_corresponding(wi, exclude=("yale",)))
    df = pd.concat([iw, sw, swn], ignore_index=True).rename(columns={"institution_key": "entity"})
    df["period"] = df.publication_year.map(m.period)
    return df


def entity_name(e: str) -> str:
    return {"statewide": "Connecticut (all 17 institutions)",
            "statewide_no_yale": "Connecticut without Yale"}.get(e, NAMES.get(e, e))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    works, wi = load()
    df = entities(works, wi)
    complete = df[df.period == "complete"]
    written = {}

    def save(name, table, note):
        table = table.copy()
        if "entity" in table:
            table.insert(1, "entity_name", table.entity.map(entity_name))
        table.to_csv(OUT / f"{name}.csv", index=False)
        written[name] = {"rows": len(table), "note": note}

    # Q1, Q2: OA status by year, and pooled summaries
    save("oa_category_by_year", m.oa_breakdown(df, ["entity", "publication_year", "period"]),
         "Works and share by OA category, per entity and year. 2026 is incomplete. "
         "diamond = fee confirmed $0; oa_fee_unconfirmed = OpenAlex diamond without a confirmed $0 fee.")
    save("oa_category_2015_2025", m.oa_breakdown(complete, ["entity"]),
         "Works and share by OA category, 2015-2025 pooled.")
    save("free_to_read_by_year", m.free_to_read_summary(df, ["entity", "publication_year", "period"]),
         "Share of works free to read (any status but closed), per year.")
    save("free_to_read_2015_2025", m.free_to_read_summary(complete, ["entity"]),
         "Share free to read, 2015-2025 pooled.")

    # Q3: fields, topics, publishers (2015-2025)
    save("fields_2015_2025", m.top_groups(complete, ["entity"], "field_name", n=10),
         "OpenAlex fields: top 10 by output and top 10 by closed works, 2015-2025.")
    save("topics_2015_2025", m.top_groups(complete, ["entity"], "topic_name", n=10),
         "OpenAlex topics: top 10 by output and top 10 by closed works, 2015-2025.")
    save("publishers_2015_2025", m.top_groups(complete, ["entity"], "publisher_parent_name", n=10),
         "Publishers (top of OpenAlex host organization lineage): top 10 by output and by closed works, 2015-2025.")

    # Q4: APC estimates
    apc_year = pd.concat([m.apc_estimate(df, ["entity", "publication_year", "period"], corresponding_only=c)
                          for c in (False, True)], ignore_index=True)
    save("apc_estimates_by_year", apc_year,
         "ESTIMATE. List-price APCs for gold and hybrid works (oa_fee_unconfirmed works are not counted). Two methods: upper bound (all authors) "
         "and corresponding-author attribution. Not actual payments.")
    apc_pooled = pd.concat([m.apc_estimate(complete, ["entity"], corresponding_only=c)
                            for c in (False, True)], ignore_index=True)
    save("apc_estimates_2015_2025", apc_pooled, "ESTIMATE. As above, 2015-2025 pooled.")
    save("corresponding_coverage", m.corresponding_coverage(df, ["entity", "period"]),
         "Works with any corresponding institution recorded in OpenAlex.")

    # Books and chapters (separate count, from the phase 1 group_by queries)
    cand = pd.read_parquet(DERIVED / "institution_candidates.parquet")
    books = []
    for key, name, ids, _ in INSTITUTIONS:
        r = cand[cand.openalex_id == "|".join(ids)].iloc[0]
        books.append({"entity": key, "books_and_chapters_2015_2025": int(r.books_chapters_2015_2025),
                      "all_types_2015_2025": int(r.all_types_2015_2025)})
    save("books_and_chapters_2015_2025", pd.DataFrame(books),
         "Books and book chapters counted separately (not in OA or APC metrics). From OpenAlex group_by.")

    manifest = {"snapshot_date": snapshot()["snapshot_date"],
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "works_in_scope": int(len(works)), "tables": written,
                "scope": "Articles and reviews, not retracted, 2015-2026, 17 Connecticut institutions; "
                         "repository records without a DOI, meeting abstracts and known affiliation errors excluded."}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for k, v in written.items():
        print(f"{k}: {v['rows']} rows")


if __name__ == "__main__":
    main()
