"""Phase 6, step 7: one small table of headline cross-check results.

Plain-language summary: reads the cross-check tables written by s07 to s11 and
writes the few agreement figures the Methods page quotes, each with its
numerator and denominator, so every number on that page traces to a file.
Definitions match docs/crosschecks.md:
- Unpaywall agrees if its status equals OpenAlex's (Unpaywall has no
  "diamond", so OpenAlex diamond counts as gold).
- OpenAIRE free to read: OpenAlex status other than closed vs OpenAIRE
  best access right OPEN. Records with no access value are reported apart.
- DOAJ: OpenAlex's "in DOAJ" flag vs finding the journal in DOAJ.

Output: data/derived/crosschecks/summary.csv
"""
from __future__ import annotations

import csv

import pandas as pd

from pipeline.config import DERIVED

C = DERIVED / "crosschecks"


def main() -> None:
    s = pd.read_csv(C / "sample.csv")
    u = s.merge(pd.read_csv(C / "unpaywall_sample.csv"), on=["work_id", "doi"])
    o = s.merge(pd.read_csv(C / "openaire_sample.csv"), on=["work_id", "doi"])
    j = pd.read_csv(C / "doaj_journals.csv")
    rows = []

    def add(metric, num, den, note=""):
        rows.append({"metric": metric, "numerator": int(num), "denominator": int(den),
                     "share": round(num / den, 4) if den else None, "note": note})

    add("sample_size", len(s), len(s), "30 articles per institution, 2015-2025, with a DOI")
    uf = u[u.found == True]
    add("unpaywall_found", len(uf), len(u))
    add("unpaywall_status_agrees", (uf.oa_status.replace({"diamond": "gold"}) == uf.upw_oa_status).sum(), len(uf),
        "not independent: Unpaywall runs on the OpenAlex database")
    of = o[o.found == True]
    add("openaire_found", len(of), len(o))
    blank = of.oaire_access.isna()
    add("openaire_no_access_value", blank.sum(), len(of), "OpenAIRE has no access information for these")
    ans = of[~blank]
    agree = (ans.oa_status != "closed") == (ans.oaire_access == "OPEN")
    add("openaire_free_to_read_agrees", agree.sum(), len(ans), "where OpenAIRE gives an access value")
    add("openaire_closed_but_openaire_open", ((ans.oa_status == "closed") & (ans.oaire_access == "OPEN")).sum(), len(ans))
    add("openaire_free_but_openaire_not_open", ((ans.oa_status != "closed") & (ans.oaire_access != "OPEN")).sum(), len(ans))
    add("doaj_flag_agrees", (j.openalex_is_in_doaj == j.in_doaj).sum(), len(j), "journals checked")
    with (C / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
