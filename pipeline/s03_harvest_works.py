"""Step 2a: download full records for every in-scope work, one year at a time.

Scope: articles and reviews, not retracted, 2015-2026, with at least one author
at one of the 17 OpenAlex IDs in pipeline/institutions.py. One combined filter
returns each work once, so collaborations are not downloaded twice.

Cost: 1 credit per page of 100 works (confirmed by the X-RateLimit-Credits-Used
header). Pages are cached, so rerunning after an interruption costs nothing for
pages already saved. Run: python -m pipeline.s03_harvest_works [year ...]
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

from pipeline.config import COMPLETE_YEARS, CORE_TYPES, INCOMPLETE_YEAR
from pipeline.institutions import ALL_IDS
from pipeline.openalex import get

SCRIPT = "s03_harvest_works"
SELECT = ",".join([
    "id", "doi", "title", "publication_year", "publication_date", "type", "language",
    "open_access", "primary_location", "locations", "best_oa_location",
    "apc_list", "apc_paid", "corresponding_institution_ids", "corresponding_author_ids",
    "authorships", "primary_topic", "is_retracted",
])
YEARS = list(range(COMPLETE_YEARS[0], INCOMPLETE_YEAR + 1))


def work_filter(year: int) -> str:
    return (f"authorships.institutions.lineage:{'|'.join(ALL_IDS)},publication_year:{year},"
            f"type:{'|'.join(CORE_TYPES)},is_retracted:false")


def pages(year: int):
    """Yield every page of results for one year, following the cursor."""
    cursor = "*"
    while cursor:
        body = get("works", {"filter": work_filter(year), "select": SELECT,
                             "per_page": 100, "cursor": cursor}, SCRIPT, log_cache_hits=False)
        yield body
        cursor = body["meta"].get("next_cursor") if body["results"] else None


def harvest_year(year: int) -> tuple[int, int, int]:
    n_pages = n_works = expected = 0
    for body in pages(year):
        expected = body["meta"]["count"]
        n_pages += 1
        n_works += len(body["results"])
        if n_pages % 25 == 0:
            print(f"  {year}: {n_works:,} / {expected:,}", flush=True)
    print(f"{year}: done, {n_works:,} works in {n_pages} pages (API count {expected:,})", flush=True)
    return year, n_works, expected


def main(years=YEARS):
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(harvest_year, years))
    bad = [r for r in results if r[1] != r[2]]
    print("ALL YEARS MATCH API COUNTS" if not bad else f"MISMATCH: {bad}")
    return results


if __name__ == "__main__":
    main([int(y) for y in sys.argv[1:]] or YEARS)
