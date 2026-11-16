"""Phase 6, step 5: compare list prices with fees actually paid (OpenAPC).

Plain-language summary: OpenAPC collects the article fees universities really
paid, reported by the universities themselves (mostly in Europe). No
Connecticut institution reports to it, so it cannot show Connecticut spending.
It can show how far list prices, which our APC estimates use, sit from what is
actually paid. Two comparisons:

1. Same articles. Connecticut articles whose fee was paid by a co-author's
   institution that reports to OpenAPC. For each, the fee paid (euros, incl.
   VAT) is set against the journal's current euro list price in OpenAlex.
2. Same journals. For every gold or hybrid Connecticut article 2015-2025, the
   median fee paid for that journal in OpenAPC (2015 or later, at least 5
   payments) is set against the journal's euro list price.

Both compare in euros, so no currency conversion is needed. List prices are
today's prices and fees paid are from the year paid, so part of any gap is
price rises over time. That is the point the Methods page needs to make.

License: OpenAPC is ODbL 1.0. The per-article match table is an adapted
database, so it is written to crosschecks/openapc/ under ODbL. The summary
figures are produced works and only need attribution.

Outputs (data/derived/crosschecks/):
- openapc/openapc_ct_matches.csv   (ODbL) one row per matched article
- openapc_summary.csv              summary ratios
"""
from __future__ import annotations

import csv
import statistics as st

import duckdb

from pipeline.config import COMPLETE_YEARS, CORE_TYPES, DERIVED
from pipeline.openalex import get
from pipeline.sources import get_file

OUT = DERIVED / "crosschecks"
SCRIPT = "s11_openapc"
URL = "https://raw.githubusercontent.com/OpenAPC/openapc-de/master/data/apc_de.csv"
LO, HI = COMPLETE_YEARS
TYPES = ",".join(f"'{t}'" for t in CORE_TYPES)
MIN_PAYMENTS = 5


def eur_list_prices(con, source_ids: list[str]) -> dict[str, float]:
    out = {}
    for i in range(0, len(source_ids), 100):
        body = get("sources", {"filter": "openalex:" + "|".join(source_ids[i:i + 100]), "per_page": 100,
                               "select": "id,apc_prices"}, SCRIPT)
        for s in body["results"]:
            eur = [p["price"] for p in s.get("apc_prices") or [] if p.get("currency") == "EUR"]
            if eur and max(eur) > 0:  # a 0 list price would make the ratio meaningless
                out[s["id"].split("/")[-1]] = float(max(eur))
    return out


def summarise(label: str, pairs: list[tuple[float, float]]) -> dict:
    """pairs = (paid, list). Ratio of totals and median of per-article ratios."""
    if not pairs:
        return {"comparison": label, "articles": 0}
    paid, lst = sum(p for p, _ in pairs), sum(l for _, l in pairs)
    return {"comparison": label, "articles": len(pairs),
            "total_paid_eur": round(paid), "total_list_eur": round(lst),
            "paid_as_share_of_list": round(paid / lst, 3),
            "median_article_ratio": round(st.median(p / l for p, l in pairs), 3)}


def main() -> None:
    (OUT / "openapc").mkdir(parents=True, exist_ok=True)
    path = get_file("openapc", URL, "apc_de.csv", SCRIPT).as_posix()
    con = duckdb.connect()
    con.execute(f"create view apc as select lower(doi) doi, try_cast(period as int) period, try_cast(euro as double) euro, "
                f"is_hybrid, issn_l, institution from read_csv('{path}', all_varchar=true)")
    con.execute(f"""create view ct as select work_id, lower(replace(doi,'https://doi.org/','')) doi, publication_year,
        oa_category, source_id, source_name, source_issn_l from '{DERIVED / "works.parquet"}'
        where in_scope and type in ({TYPES}) and publication_year between {LO} and {HI}""")

    # 1. Same articles
    matches = con.execute("""select ct.work_id, ct.doi, ct.publication_year, ct.oa_category, ct.source_id,
        ct.source_name, apc.period, apc.euro, apc.is_hybrid, apc.institution
        from apc join ct using (doi) order by ct.work_id, apc.institution""").fetchall()
    cols = ["work_id", "doi", "publication_year", "oa_category", "source_id", "journal",
            "openapc_period", "openapc_euro", "openapc_is_hybrid", "openapc_institution"]
    rows = [dict(zip(cols, m)) for m in matches]

    # 2. Same journals
    bench = con.execute(f"""select issn_l, median(euro) med, count(*) n from apc
        where period >= {LO} and euro > 0 and issn_l is not null group by 1 having count(*) >= {MIN_PAYMENTS}""").fetchall()
    bench = {b[0]: (b[1], b[2]) for b in bench}
    paid_works = con.execute("select work_id, source_id, source_issn_l, oa_category, publication_year from ct "
                             "where oa_category in ('gold','hybrid')").fetchall()

    ids = sorted({r["source_id"] for r in rows if r["source_id"]} | {w[1] for w in paid_works if w[1]})
    eur = eur_list_prices(con, ids)
    for r in rows:
        r["openalex_list_eur_today"] = eur.get(r["source_id"])
    fields = cols + ["openalex_list_eur_today"]
    with (OUT / "openapc" / "openapc_ct_matches.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    summary = []
    for cat in ("gold", "hybrid"):
        pairs = [(r["openapc_euro"], r["openalex_list_eur_today"]) for r in rows
                 if r["oa_category"] == cat and r["openapc_euro"] and r["openalex_list_eur_today"]]
        summary.append(summarise(f"same articles, {cat}", pairs))
        for lo, hi in ((LO, 2019), (2020, HI)):
            summary.append(summarise(f"same articles, {cat}, published {lo}-{hi}",
                                     [(r["openapc_euro"], r["openalex_list_eur_today"]) for r in rows
                                      if r["oa_category"] == cat and lo <= r["publication_year"] <= hi
                                      and r["openapc_euro"] and r["openalex_list_eur_today"]]))
        works = [w for w in paid_works if w[3] == cat]
        pairs = [(bench[w[2]][0], eur[w[1]]) for w in works if w[2] in bench and w[1] in eur]
        s = summarise(f"same journals, {cat}", pairs)
        s["ct_works_in_category"] = len(works)
        s["coverage"] = round(len(pairs) / len(works), 3) if works else None
        summary.append(s)
    scoap3 = [r for r in rows if r["oa_category"] in ("diamond", "oa_fee_unconfirmed")]
    summary.append({"comparison": "no-author-fee works with an OpenAPC payment (library-funded, e.g. SCOAP3)",
                    "articles": len({r["work_id"] for r in scoap3}),
                    "total_paid_eur": round(sum(r["openapc_euro"] or 0 for r in scoap3))})
    with (OUT / "openapc_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for s in summary for k in s)))
        w.writeheader()
        w.writerows(summary)
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
