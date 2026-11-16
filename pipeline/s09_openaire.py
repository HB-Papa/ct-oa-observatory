"""Phase 6, step 3: look up the sample in the OpenAIRE Graph.

Plain-language summary: OpenAIRE is a European research graph built separately
from OpenAlex, and it is strong on repository copies. This asks it about the
510 sample DOIs, 50 at a time (11 requests, well under the 60 per hour allowed
without a token), and records:
- whether OpenAIRE lists the article as open (bestAccessRight = OPEN)
- its publisher OA color (gold, hybrid, bronze, or none)
- whether it marks the article green (a repository copy exists)
- whether it says the journal is diamond

OpenAIRE data is CC BY, so these per-article results credit OpenAIRE.

Output: data/derived/crosschecks/openaire_sample.csv
"""
from __future__ import annotations

import csv

from pipeline.config import DERIVED
from pipeline.sources import get_json

OUT = DERIVED / "crosschecks"
BATCH = 50
FIELDS = ["work_id", "doi", "found", "oaire_access", "oaire_color", "oaire_is_green",
          "oaire_in_diamond_journal", "oaire_n_records"]


def main() -> None:
    sample = list(csv.DictReader((OUT / "sample.csv").open(encoding="utf-8")))
    by_doi: dict[str, list[dict]] = {}
    for i in range(0, len(sample), BATCH):
        dois = sorted(r["doi"] for r in sample[i:i + BATCH])
        _, body = get_json("openaire", "https://api.openaire.eu/graph/v4/research-products",
                           {"filter": "ids.doi:" + "|".join(dois), "pageSize": "100"},
                           "s09_openaire", min_interval=1.0)
        if body["header"]["numFound"] > 100:
            raise RuntimeError("more than one page of results; lower BATCH")
        wanted = set(dois)
        for rec in body.get("results", []):
            for p in rec.get("pids") or []:
                if p.get("scheme") == "doi" and p.get("value", "").lower() in wanted:
                    by_doi.setdefault(p["value"].lower(), []).append(rec)

    rows = []
    for r in sample:
        recs = by_doi.get(r["doi"], [])
        if not recs:
            rows.append({"work_id": r["work_id"], "doi": r["doi"], "found": False})
            continue
        # OpenAIRE sometimes keeps more than one record per DOI. Combine them:
        # open if any record is open, green if any says green.
        access = {(x.get("bestAccessRight") or {}).get("label") for x in recs}
        colors = {x.get("openAccessColor") for x in recs} - {None}
        rows.append({"work_id": r["work_id"], "doi": r["doi"], "found": True,
                     "oaire_access": "OPEN" if "OPEN" in access else "|".join(sorted(a for a in access if a)) or None,
                     "oaire_color": "|".join(sorted(colors)) or None,
                     "oaire_is_green": any(x.get("isGreen") for x in recs),
                     "oaire_in_diamond_journal": any(x.get("isInDiamondJournal") for x in recs),
                     "oaire_n_records": len(recs)})
    with (OUT / "openaire_sample.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"openaire: {sum(r['found'] for r in rows)} of {len(rows)} found")


if __name__ == "__main__":
    main()
