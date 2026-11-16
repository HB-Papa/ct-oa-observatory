"""Step 1b: count works per candidate institution, 2015-2026.

For each candidate, two group_by queries (1 credit each, cached):
- articles + reviews, not retracted, grouped by publication year
- all work types except paratext, not retracted, 2015-2025, grouped by type
A work counts for an institution if any author lists it or one of its
sub-units (OpenAlex "lineage"). Also counted: UConn + UConn Health together,
and statewide totals with and without Yale, each deduplicated by work ID
(one query with OR'd IDs returns each work once).
"""
from __future__ import annotations

import pandas as pd

from pipeline.config import BOOK_TYPES, COMPLETE_YEARS, CORE_TYPES, DERIVED, INCOMPLETE_YEAR
from pipeline.openalex import get

SCRIPT = "s02_institution_counts"

# The 16 institutions named in the project brief (UConn Health rolls up into UConn).
NAMED = {
    "I32971472": "Yale University", "I140172145": "University of Connecticut",
    "I75929689": "UConn Health", "I100538780": "Wesleyan University",
    "I56722557": "Trinity College", "I4498119": "Connecticut College",
    "I43267033": "Quinnipiac University", "I126350171": "Fairfield University",
    "I130186095": "Sacred Heart University", "I162281398": "University of Hartford",
    "I40253897": "University of New Haven", "I35462925": "Southern Connecticut State University",
    "I154264771": "Central Connecticut State University",
    "I204366597": "Western Connecticut State University",
    "I203331390": "Eastern Connecticut State University",
    "I186274478": "United States Coast Guard Academy",
}
SUGGEST_MIN_ALL_TIME = 40  # other CT "education" institutions at or above this are counted too
NOT_COLLEGES = ("Public Schools", "Public School", "Choate", "Kingswood", "Pomfret",
                "Magnet", "Villa Maria", "Elementary", "American School for the Deaf",
                "Access Technologies", "Goldratt")


def year_counts(lineage_filter: str) -> dict[int, int]:
    f = (f"authorships.institutions.lineage:{lineage_filter},"
         f"publication_year:{COMPLETE_YEARS[0]}-{INCOMPLETE_YEAR},"
         f"type:{'|'.join(CORE_TYPES)},is_retracted:false")
    body = get("works", {"filter": f, "group_by": "publication_year"}, SCRIPT)
    return {int(g["key"]): g["count"] for g in body["group_by"]}


def type_counts(lineage_filter: str) -> dict[str, int]:
    f = (f"authorships.institutions.lineage:{lineage_filter},"
         f"publication_year:{COMPLETE_YEARS[0]}-{COMPLETE_YEARS[1]},"
         f"type:!paratext,is_retracted:false")
    body = get("works", {"filter": f, "group_by": "type"}, SCRIPT)
    return {g["key"].rsplit("/", 1)[-1]: g["count"] for g in body["group_by"]}


def row(label: str, ids: str, role: str) -> dict:
    yc, tc = year_counts(ids), type_counts(ids)
    complete = sum(v for y, v in yc.items() if COMPLETE_YEARS[0] <= y <= COMPLETE_YEARS[1])
    return {"openalex_id": ids, "name": label, "role": role,
            "articles_reviews_2015_2025": complete,
            "articles_reviews_2025": yc.get(2025, 0),
            "articles_reviews_2026_incomplete": yc.get(INCOMPLETE_YEAR, 0),
            "books_chapters_2015_2025": sum(tc.get(t, 0) for t in BOOK_TYPES),
            "all_types_2015_2025": sum(tc.values()),
            **{f"y{y}": yc.get(y, 0) for y in range(COMPLETE_YEARS[0], INCOMPLETE_YEAR + 1)}}


def main() -> pd.DataFrame:
    inst = pd.read_parquet(DERIVED / "ct_institutions_all.parquet")
    meta = inst.set_index("openalex_id")
    suggested = inst[(inst.type == "education") & (inst.works_count_all_time >= SUGGEST_MIN_ALL_TIME)
                     & ~inst.openalex_id.isin(NAMED)
                     & ~inst.name.str.contains("|".join(NOT_COLLEGES))]
    rows = [row(n, i, "named") for i, n in NAMED.items()]
    rows += [row(r.name, r.openalex_id, "suggested") for r in suggested.itertuples()]
    uconn = "I140172145|I75929689"
    rows.append(row("UConn + UConn Health (deduplicated)", uconn, "rollup"))
    all_ids = "|".join(list(NAMED) + suggested.openalex_id.tolist())
    no_yale = "|".join(i for i in all_ids.split("|") if i != "I32971472")
    rows.append(row("Statewide, named + suggested (deduplicated)", all_ids, "statewide"))
    rows.append(row("Statewide without Yale (deduplicated)", no_yale, "statewide"))
    named_ids = "|".join(NAMED)
    rows.append(row("Statewide, named only (deduplicated)", named_ids, "statewide"))
    df = pd.DataFrame(rows)
    df["lineage"] = df.openalex_id.map(lambda i: meta.lineage.get(i, ""))
    df["type"] = df.openalex_id.map(lambda i: meta.type.get(i, ""))
    df.to_parquet(DERIVED / "institution_candidates.parquet", index=False)
    df.drop(columns=[c for c in df if c.startswith("y")]).to_csv(
        DERIVED / "institution_candidates.csv", index=False)
    return df


if __name__ == "__main__":
    out = main()
    cols = ["openalex_id", "name", "role", "articles_reviews_2015_2025",
            "articles_reviews_2026_incomplete", "books_chapters_2015_2025", "all_types_2015_2025"]
    print(out[cols].to_string(max_colwidth=40))
