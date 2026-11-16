"""Step 1a: list Connecticut institutions known to OpenAlex.

Two keyless-friendly queries (1 credit each), both cached:
- the 100 Connecticut institutions with the most works (any type, all years)
- every Connecticut institution OpenAlex classes as "education"
The union is written to data/derived/ct_institutions_all.parquet.
"""
from __future__ import annotations

import pandas as pd

from pipeline.config import DERIVED
from pipeline.openalex import get

SCRIPT = "s01_institutions_list"
SELECT = "id,display_name,type,lineage,ror,works_count,geo"


def fetch(filter_: str, sort: str = "works_count:desc") -> list[dict]:
    body = get("institutions", {"filter": filter_, "sort": sort, "per_page": 100,
                                "select": SELECT}, SCRIPT)
    print(f"{filter_}: {body['meta']['count']} matches, {len(body['results'])} returned")
    return body["results"]


def main() -> pd.DataFrame:
    rows = {r["id"]: r for r in fetch("geo.region:Connecticut")}
    rows |= {r["id"]: r for r in fetch("geo.region:Connecticut,type:education")}
    df = pd.DataFrame([{
        "openalex_id": r["id"].rsplit("/", 1)[-1],
        "name": r["display_name"],
        "type": r["type"],
        "city": (r.get("geo") or {}).get("city"),
        "ror": r.get("ror"),
        "lineage": "|".join(x.rsplit("/", 1)[-1] for x in r.get("lineage") or []),
        "works_count_all_time": r["works_count"],
    } for r in rows.values()]).sort_values("works_count_all_time", ascending=False)
    DERIVED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DERIVED / "ct_institutions_all.parquet", index=False)
    return df


if __name__ == "__main__":
    out = main()
    print(out.to_string(max_rows=80, max_colwidth=45))
