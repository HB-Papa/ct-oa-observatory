"""Cross-check agent, part 8: spot checks of the OpenAPC match table.

No network. Picks 10 matched rows at random (fixed seed) and prints them beside the OpenAlex
work's DOI, journal and year, and runs simple plausibility checks over all rows.
Run: python -m verification.crosscheck_openapc"""
import duckdb
from pipeline.config import DERIVED
con = duckdb.connect()
M = f"read_csv('{(DERIVED / 'crosschecks' / 'openapc' / 'openapc_ct_matches.csv').as_posix()}')"
W = f"'{(DERIVED / 'works.parquet').as_posix()}'"
def show(t, q):
    print(f"\n### {t}\n"); print(con.execute(q).df().to_markdown(index=False))
show("Rows, distinct works, categories", f"select oa_category, count(*) rows_, count(distinct work_id) works from {M} group by 1 order by 2 desc")
show("Works matched by more than one OpenAPC row", f"select count(*) from (select work_id from {M} group by 1 having count(*)>1)")
show("Euro value range", f"select min(openapc_euro) mn, median(openapc_euro) med, max(openapc_euro) mx, count(*) filter (where openapc_euro<=0) zero_or_less from {M}")
show("DOI match check: matched DOI equals OpenAlex DOI (lowercased, prefix removed)",
     f"""select count(*) rows_, count(*) filter (where lower(replace(w.doi,'https://doi.org/',''))=m.doi) same,
         count(*) filter (where w.publication_year = m.publication_year) same_year,
         count(*) filter (where abs(m.openapc_period - m.publication_year) <= 1) period_within_1y
         from {M} m join {W} w using (work_id)""")
show("10 random rows (seed 7)", f"""select setseed(0.7); """) if False else None
con.execute("select setseed(0.7)")
show("10 random rows", f"""select m.work_id, m.doi, m.publication_year yr, m.oa_category cat, m.journal, m.openapc_period period,
    m.openapc_euro eur_paid, m.openapc_is_hybrid hyb, m.openapc_institution, m.openalex_list_eur_today list_eur
    from {M} m order by random() limit 10""")
show("Extreme ratios (paid / list < 0.3 or > 1.5)", f"""select work_id, journal, publication_year, oa_category, openapc_period, openapc_euro, openalex_list_eur_today,
    round(openapc_euro/openalex_list_eur_today,2) ratio, openapc_institution from {M}
    where openalex_list_eur_today > 0 and (openapc_euro/openalex_list_eur_today < 0.3 or openapc_euro/openalex_list_eur_today > 1.5) order by ratio limit 15""")
show("Category vs OpenAPC is_hybrid", f"select oa_category, openapc_is_hybrid, count(*) n from {M} group by all order by 1,2")
show("No-author-fee works with an OpenAPC payment: journals and payers",
     f"""select journal, openapc_institution, count(distinct work_id) works, round(median(openapc_euro)) med_eur from {M}
         where oa_category in ('diamond','oa_fee_unconfirmed') group by all order by works desc limit 12""")
show("Diamond / fee-not-confirmed works with an OpenAPC payment, split SCOAP3 physics vs other",
     f"""select oa_category, case when journal in ('Journal of High Energy Physics','The European Physical Journal C','Physics Letters B',
         'Nuclear Physics B','Chinese Physics C','Progress of Theoretical and Experimental Physics','Advances in High Energy Physics') then 'SCOAP3 journal' else 'other' end grp,
         count(distinct work_id) works, round(sum(openapc_euro)) eur, round(median(openapc_euro)) med
         from {M} where oa_category in ('diamond','oa_fee_unconfirmed') group by all order by 1,2""")
show("Diamond works with an OpenAPC payment outside SCOAP3 journals",
     f"""select work_id, journal, publication_year, openapc_euro, openapc_institution from {M}
         where oa_category='diamond' and journal not in ('Journal of High Energy Physics','The European Physical Journal C','Physics Letters B')""")
