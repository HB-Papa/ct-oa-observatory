"""Phase 6, step 4: check journals against DOAJ.

Plain-language summary: DOAJ (Directory of Open Access Journals) is the vetted
list of fully open access journals and records whether each one charges an
article fee. This step:

1. Takes three groups of journals:
   a. journals of works OpenAlex calls "diamond" but with no fee recorded
      (our "fee not confirmed" category, 8,349 works in 2015-2025)
   b. journals of works we call diamond (fee confirmed $0)
   c. the 50 journals with the most Connecticut articles, and the 50 fully
      open access journals with the most Connecticut articles
2. Gets each journal's ISSNs from OpenAlex (one request per 100 journals).
3. Looks them up in DOAJ (journal records, CC0) and saves what DOAJ says:
   listed or not, fee or no fee, the year the journal became open access.
4. For group (a), works out what DOAJ would say about each work: no fee, fee,
   or not listed. DOAJ shows a journal's current policy, so a work only gets a
   DOAJ answer if it was published in or after the journal's open access start
   year. This result is reported on its own and does NOT change site figures
   unless Chris approves it (see DECISIONS.md).

Outputs (data/derived/crosschecks/):
- doaj_journals.csv            one row per journal checked
- doaj_fee_unconfirmed.csv     group (a) works counted by DOAJ answer, statewide and per institution
- doaj_top_journals.csv        group (c) with OpenAlex vs DOAJ side by side
"""
from __future__ import annotations

import csv
from urllib.parse import quote

import duckdb

from pipeline.config import COMPLETE_YEARS, CORE_TYPES, DERIVED
from pipeline.institutions import INSTITUTIONS
from pipeline.openalex import get
from pipeline.sources import get_json

OUT = DERIVED / "crosschecks"
SCRIPT = "s10_doaj"
W = f"'{DERIVED / 'works.parquet'}'"
WI = f"'{DERIVED / 'work_institutions.parquet'}'"
LO, HI = COMPLETE_YEARS
TYPES = ",".join(f"'{t}'" for t in CORE_TYPES)
SCOPE = f"w.in_scope and w.type in ({TYPES}) and w.publication_year between {LO} and {HI}"


def journal_groups(con) -> dict[str, set[str]]:
    q = lambda s: {r[0] for r in con.execute(s).fetchall() if r[0]}
    return {
        "fee_unconfirmed": q(f"select distinct source_id from {W} w where {SCOPE} and oa_category='oa_fee_unconfirmed'"),
        "diamond": q(f"select distinct source_id from {W} w where {SCOPE} and oa_category='diamond'"),
        "top50_all": q(f"""select source_id from {W} w where {SCOPE} and source_id is not null
                          group by 1 order by count(*) desc, 1 limit 50"""),
        "top50_oa": q(f"""select source_id from {W} w where {SCOPE} and source_id is not null and source_is_oa
                         group by 1 order by count(*) desc, 1 limit 50"""),
    }


def openalex_sources(ids: list[str]) -> dict[str, dict]:
    out = {}
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        body = get("sources", {"filter": "openalex:" + "|".join(chunk), "per_page": 100,
                               "select": "id,display_name,issn_l,issn,is_in_doaj,is_oa,apc_usd,host_organization_name"},
                   SCRIPT)
        for s in body["results"]:
            out[s["id"].split("/")[-1]] = s
    return out


def doaj_lookup(sources: dict[str, dict]) -> dict[str, dict]:
    """Return DOAJ's record for each source, matched on any of its ISSNs."""
    issn_to_src: dict[str, str] = {}
    for sid, s in sources.items():
        for issn in s.get("issn") or ([s["issn_l"]] if s.get("issn_l") else []):
            issn_to_src[issn.upper()] = sid
    issns = sorted(issn_to_src)
    found: dict[str, dict] = {}
    for i in range(0, len(issns), 40):
        chunk = issns[i:i + 40]
        query = "issn:(" + " OR ".join(f'"{x}"' for x in chunk) + ")"
        _, body = get_json("doaj", "https://doaj.org/api/search/journals/" + quote(query, safe=""),
                           {"pageSize": "100"}, SCRIPT, min_interval=0.6)
        if body.get("total", 0) > 100:
            raise RuntimeError("more than one page of DOAJ results; lower the chunk size")
        for rec in body.get("results", []):
            bj = rec["bibjson"]
            for issn in (bj.get("pissn"), bj.get("eissn")):
                if issn and issn.upper() in issn_to_src:
                    found[issn_to_src[issn.upper()]] = rec
    return found


def journal_row(sid: str, s: dict | None, rec: dict | None) -> dict:
    row = {"source_id": sid, "journal": (s or {}).get("display_name"),
           "openalex_is_in_doaj": (s or {}).get("is_in_doaj"), "openalex_is_oa": (s or {}).get("is_oa"),
           "openalex_apc_usd": (s or {}).get("apc_usd"), "in_doaj": rec is not None}
    if rec:
        bj = rec["bibjson"]
        apc = bj.get("apc") or {}
        usd = [p["price"] for p in apc.get("max") or [] if p.get("currency") == "USD"]
        row |= {"doaj_has_apc": apc.get("has_apc"),
                "doaj_max_apc_usd": max(usd) if usd else None,
                "doaj_max_apc_other": "|".join(f"{p['price']} {p['currency']}" for p in apc.get("max") or []
                                               if p.get("currency") != "USD") or None,
                "doaj_has_other_charges": (bj.get("other_charges") or {}).get("has_other_charges"),
                "doaj_oa_start": bj.get("oa_start"),
                "doaj_added": (rec.get("created_date") or "")[:10]}
    return row


def classify(year: int, j: dict | None) -> str:
    """What DOAJ says about one 'fee not confirmed' work."""
    if not j or not j.get("in_doaj"):
        return "not_in_doaj"
    start = j.get("doaj_oa_start")
    if start and int(start) > year:
        return "published_before_doaj_oa_start"
    if j.get("doaj_has_apc") is False:
        return "doaj_no_fee" if not j.get("doaj_has_other_charges") else "doaj_no_apc_but_other_charges"
    if j.get("doaj_has_apc") is True:
        return "doaj_charges_fee"
    return "doaj_fee_unknown"


def write(name: str, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    groups = journal_groups(con)
    all_ids = sorted(set().union(*groups.values()))
    sources = openalex_sources(all_ids)
    doaj = doaj_lookup(sources)
    journals = {sid: journal_row(sid, sources.get(sid), doaj.get(sid)) for sid in all_ids}
    for sid, row in journals.items():
        row["groups"] = "|".join(g for g, ids in groups.items() if sid in ids)
    write("doaj_journals.csv", sorted(journals.values(), key=lambda r: r["source_id"]))

    # Group (a): what DOAJ says about each fee-not-confirmed work
    works = con.execute(f"""select w.work_id, w.publication_year, w.source_id, list(distinct wi.institution_key)
        from {W} w join {WI} wi using (work_id)
        where {SCOPE} and wi.in_scope and w.oa_category='oa_fee_unconfirmed' group by all""").fetchall()
    counts: dict[tuple[str, str], int] = {}
    for _, year, sid, insts in works:
        c = classify(year, journals.get(sid))
        for key in ["statewide", *insts]:
            counts[(key, c)] = counts.get((key, c), 0) + 1
    order = ["statewide", *[i[0] for i in INSTITUTIONS]]
    write("doaj_fee_unconfirmed.csv",
          [{"entity": k, "doaj_answer": c, "works": n} for (k, c), n in
           sorted(counts.items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1]))])

    # Group (c): top journals side by side
    sizes = dict(con.execute(f"select source_id, count(*) from {W} w where {SCOPE} group by 1").fetchall())
    top = [journals[s] | {"ct_articles_2015_2025": sizes.get(s, 0)}
           for s in all_ids if "top50" in journals[s]["groups"]]
    write("doaj_top_journals.csv", sorted(top, key=lambda r: -r["ct_articles_2015_2025"]))
    tally = {}
    for _, year, sid, _ in works:
        c = classify(year, journals.get(sid))
        tally[c] = tally.get(c, 0) + 1
    print("journals checked:", len(all_ids), "in DOAJ:", sum(j["in_doaj"] for j in journals.values()))
    print("fee-not-confirmed works by DOAJ answer:", tally)


if __name__ == "__main__":
    main()
