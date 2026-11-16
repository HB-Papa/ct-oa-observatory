"""Cross-check agent, part 7: DOAJ summaries.

No network. Uses doaj_*.csv, works.parquet and the cached DOAJ records (for fee URLs and the
'last updated' date of a few journals). Run: python -m verification.crosscheck_doaj
"""
import glob, gzip, json
import duckdb, pandas as pd
from pipeline.config import DERIVED, RAW
C = DERIVED / "crosschecks"
con = duckdb.connect()
W = f"'{(DERIVED / 'works.parquet').as_posix()}'"
J = f"read_csv('{(C / 'doaj_journals.csv').as_posix()}')"
SC = "w.in_scope and w.type in ('article','review') and w.publication_year between 2015 and 2025"
def show(t, q):
    print(f"\n### {t}\n"); print(con.execute(q).df().to_markdown(index=False))

show("(i) fee-not-confirmed works by DOAJ answer (statewide)",
     f"select doaj_answer, works, round(100.0*works/sum(works) over (),1) pct from read_csv('{(C/'doaj_fee_unconfirmed.csv').as_posix()}') where entity='statewide' order by works desc")
show("(i) fee-not-confirmed works: is the journal in DOAJ, by OpenAlex is_in_doaj",
     f"""select w.source_is_in_doaj, j.in_doaj, count(*) works from {W} w left join {J} j using (source_id)
         where {SC} and w.oa_category='oa_fee_unconfirmed' group by all order by 1,2""")
show("(i) not-in-DOAJ fee-not-confirmed works: top journals",
     f"""select w.source_name, count(*) works from {W} w left join {J} j using (source_id)
         where {SC} and w.oa_category='oa_fee_unconfirmed' and not coalesce(j.in_doaj,false) group by 1 order by 2 desc limit 10""")
show("(i) fee-charging DOAJ journals among fee-not-confirmed works: top journals",
     f"""select w.source_name, j.doaj_max_apc_usd, j.doaj_max_apc_other, count(*) works from {W} w join {J} j using (source_id)
         where {SC} and w.oa_category='oa_fee_unconfirmed' and j.doaj_has_apc and w.publication_year >= coalesce(j.doaj_oa_start,0)
         group by all order by works desc limit 10""")
show("(ii) diamond (fee confirmed $0) works by what DOAJ says about the journal",
     f"""select case when j.in_doaj is null or not j.in_doaj then 'not in DOAJ' when j.doaj_has_apc then 'DOAJ lists a fee'
                     when j.doaj_has_other_charges then 'DOAJ no APC, other charges' else 'DOAJ no fee' end doaj,
         count(*) works from {W} w left join {J} j using (source_id) where {SC} and w.oa_category='diamond' group by 1 order by 2 desc""")
show("(ii) diamond works in journals DOAJ lists with a fee, by journal",
     f"""select w.source_name, j.doaj_max_apc_usd, j.doaj_max_apc_other, j.doaj_has_other_charges, j.doaj_oa_start,
         min(w.publication_year) y0, max(w.publication_year) y1, count(*) works
         from {W} w join {J} j using (source_id) where {SC} and w.oa_category='diamond' and j.doaj_has_apc group by all order by works desc""")
show("(iii) OpenAlex is_in_doaj vs DOAJ lookup, all journals checked",
     f"select openalex_is_in_doaj, in_doaj, count(*) journals from {J} group by all order by 1,2")
show("(iii) journals OpenAlex says are in DOAJ but our ISSN lookup did not find",
     f"select source_id, journal from {J} where openalex_is_in_doaj and not in_doaj")
top = pd.read_csv(C / "doaj_top_journals.csv")
t = top[top.in_doaj == True].copy()
t["diff_usd"] = t.doaj_max_apc_usd - t.openalex_apc_usd
t["diff_pct"] = (100 * t.diff_usd / t.openalex_apc_usd).round(1)
print("\n### (iv) top journals in DOAJ: OpenAlex apc_usd vs DOAJ max USD\n")
print(f"top journals: {len(top)}, in DOAJ: {len(t)}, both prices: {t.diff_usd.notna().sum()}, "
      f"equal: {(t.diff_usd == 0).sum()}, DOAJ higher: {(t.diff_usd > 0).sum()}, DOAJ lower: {(t.diff_usd < 0).sum()}, "
      f"median diff %: {t.diff_pct.median()}")
print(t.sort_values("ct_articles_2015_2025", ascending=False)[["journal", "ct_articles_2015_2025", "openalex_apc_usd",
      "doaj_max_apc_usd", "doaj_max_apc_other", "diff_usd", "diff_pct"]].head(25).to_markdown(index=False))
print("\nNot in DOAJ but OpenAlex says the journal is OA (top journals):")
print(top[(top.in_doaj != True) & (top.openalex_is_oa == True)][["journal", "ct_articles_2015_2025", "openalex_is_in_doaj", "openalex_apc_usd"]].to_markdown(index=False))

# Fee details from the cached DOAJ records for a few journals
want = {"Theoretical Economics", "Quantitative Economics", "BJPsych Bulletin", "International Journal of Nursing Sciences", "Current Zoology"}
seen = set()
for f in glob.glob(str(RAW / "doaj" / "*" / "*.json.gz")):
    for rec in json.loads(gzip.decompress(open(f, "rb").read()))["body"].get("results") or []:
        bj = rec["bibjson"]
        if bj.get("title") in want and bj["title"] not in seen:
            seen.add(bj["title"])
            print(f"\n{bj['title']}: apc={json.dumps(bj.get('apc'))} other_charges={json.dumps(bj.get('other_charges'))} "
                  f"waiver={json.dumps(bj.get('waiver'))} last_updated={rec.get('last_updated','')[:10]} "
                  f"publisher={(bj.get('publisher') or {}).get('name')} society={(bj.get('institution') or {}).get('name')}")

show("(ii) same, counting only works published in or after the journal's DOAJ open access start year",
     f"""select count(*) works from {W} w join {J} j using (source_id) where {SC} and w.oa_category='diamond'
         and j.doaj_has_apc and w.publication_year >= coalesce(j.doaj_oa_start, 0)""")
