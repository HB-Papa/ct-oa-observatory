"""Phase 6, step 1: draw the cross-check sample.

Plain-language summary: picks 30 articles per institution (510 in all) that
have a DOI, spread evenly over 2015-2025, so every institution and every year
is represented. The draw is repeatable: works are ordered by a hash of their ID
and a fixed seed, so rerunning picks the same works. A work co-authored by two
institutions is used once, for the first institution that drew it.

The sample is not proportional to output (small colleges are over-represented
on purpose), so the overall agreement rates are unweighted sample rates. Each
institution's rate is reported on its own too.

Output: data/derived/crosschecks/sample.csv
"""
from __future__ import annotations

import duckdb

from pipeline.config import COMPLETE_YEARS, CORE_TYPES, DERIVED
from pipeline.institutions import INSTITUTIONS

SEED = "ct-oa-observatory-phase6"
PER_INSTITUTION = 30
OUT = DERIVED / "crosschecks"


def draw(con) -> list[dict]:
    lo, hi = COMPLETE_YEARS
    types = ",".join(f"'{t}'" for t in CORE_TYPES)
    pool = con.execute(f"""
        select wi.institution_key, w.work_id, w.publication_year as year,
               lower(replace(w.doi, 'https://doi.org/', '')) as doi,
               w.oa_status, w.oa_category, w.source_id, w.source_issn_l,
               md5(w.work_id || '{SEED}') as h
        from '{DERIVED / "work_institutions.parquet"}' wi
        join '{DERIVED / "works.parquet"}' w using (work_id)
        where w.in_scope and wi.in_scope and w.doi is not null
          and w.type in ({types}) and w.publication_year between {lo} and {hi}
        order by wi.institution_key, w.publication_year, h
    """).fetchall()
    cols = ["institution_key", "work_id", "year", "doi", "oa_status", "oa_category",
            "source_id", "source_issn_l", "h"]
    by_inst: dict[str, dict[int, list[dict]]] = {}
    for r in pool:
        d = dict(zip(cols, r))
        by_inst.setdefault(d["institution_key"], {}).setdefault(d["year"], []).append(d)

    chosen, seen = [], set()
    for inst in [i[0] for i in INSTITUTIONS]:
        years = by_inst.get(inst, {})
        queues = {y: list(v) for y, v in sorted(years.items())}
        picked = 0
        while picked < PER_INSTITUTION and any(queues.values()):
            for y in list(queues):  # one per year in turn, so years stay even
                q = queues[y]
                while q and q[0]["work_id"] in seen:
                    q.pop(0)
                if not q or picked >= PER_INSTITUTION:
                    continue
                d = q.pop(0)
                seen.add(d["work_id"])
                d.pop("h")
                chosen.append(d)
                picked += 1
    return chosen


def main() -> None:
    import csv
    OUT.mkdir(parents=True, exist_ok=True)
    rows = draw(duckdb.connect())
    with (OUT / "sample.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"sample: {len(rows)} works")


if __name__ == "__main__":
    main()
