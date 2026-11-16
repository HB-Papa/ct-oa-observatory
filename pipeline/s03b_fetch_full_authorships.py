"""Step 2a (part 2): fetch full records for works whose author list was cut off.

OpenAlex list results (the pages s03 downloads) include at most 100 authorships
per work. For a work with more authors, a Connecticut author can sit past
position 100 and be invisible. Fetching the single work by ID returns every
author and costs 0 credits (confirmed with the X-RateLimit-Credits-Used header).
This step finds every harvested work with exactly 100 authorships and fetches it
individually. s04 then uses the full record for those works.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from pipeline.openalex import get
from pipeline.s03_harvest_works import SELECT, YEARS, pages

SCRIPT = "s03b_fetch_full_authorships"
AUTHOR_CAP = 100


def full_record(work_id: str) -> dict:
    return get(f"works/{work_id}", {"select": SELECT}, SCRIPT, log_cache_hits=False)


def capped_work_ids() -> list[str]:
    ids = []
    for year in YEARS:
        for body in pages(year):
            ids += [w["id"].rsplit("/", 1)[-1] for w in body["results"]
                    if len(w.get("authorships") or []) >= AUTHOR_CAP]
    return ids


def main():
    ids = capped_work_ids()
    print(f"{len(ids):,} works at the {AUTHOR_CAP}-author cap; fetching full records")
    with ThreadPoolExecutor(max_workers=8) as pool:
        sizes = list(pool.map(lambda i: len(full_record(i)["authorships"]), ids))
    print(f"done. Full author counts: min {min(sizes)}, median {sorted(sizes)[len(sizes)//2]}, max {max(sizes)}")


if __name__ == "__main__":
    main()
