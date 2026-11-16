"""Phase 6, step 2: look up the sample in Unpaywall.

Plain-language summary: asks Unpaywall about each of the 510 sample DOIs and
records its OA status and whether it lists a repository copy. Unpaywall is run
by the same nonprofit as OpenAlex and now reads from the OpenAlex database, so
this is a consistency check between two views of one dataset, not an
independent source.

The contact email Unpaywall requires is read from .env and removed from every
saved URL (see pipeline/sources.py).

Output: data/derived/crosschecks/unpaywall_sample.csv
"""
from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from pipeline.config import DERIVED
from pipeline.sources import UNPAYWALL_EMAIL, get_json

OUT = DERIVED / "crosschecks"
FIELDS = ["work_id", "doi", "found", "upw_is_oa", "upw_oa_status", "upw_has_repository_copy",
          "upw_has_accepted_repository_copy", "upw_journal_is_in_doaj"]


def lookup(row: dict) -> dict:
    status, body = get_json("unpaywall", "https://api.unpaywall.org/v2/" + quote(row["doi"], safe="/"),
                            {"email": UNPAYWALL_EMAIL}, "s08_unpaywall",
                            min_interval=0.12, ok_statuses=(200, 404))
    if status == 404:
        return {"work_id": row["work_id"], "doi": row["doi"], "found": False}
    locs = body.get("oa_locations") or []
    repo = [l for l in locs if l.get("host_type") == "repository"]
    return {"work_id": row["work_id"], "doi": row["doi"], "found": True,
            "upw_is_oa": body.get("is_oa"), "upw_oa_status": body.get("oa_status"),
            "upw_has_repository_copy": bool(repo),
            "upw_has_accepted_repository_copy": any(l.get("version") in ("acceptedVersion", "publishedVersion") for l in repo),
            "upw_journal_is_in_doaj": body.get("journal_is_in_doaj")}


def main() -> None:
    if not UNPAYWALL_EMAIL:
        raise SystemExit("Set UNPAYWALL_EMAIL in .env first.")
    sample = list(csv.DictReader((OUT / "sample.csv").open(encoding="utf-8")))
    with ThreadPoolExecutor(2) as ex:
        rows = list(ex.map(lookup, sample))
    with (OUT / "unpaywall_sample.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"unpaywall: {sum(r['found'] for r in rows)} of {len(rows)} found")


if __name__ == "__main__":
    main()
