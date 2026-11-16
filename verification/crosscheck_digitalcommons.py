"""Cross-check agent, part 6: how OpenAlex treats copies in bepress Digital Commons repositories.

Hand checks showed Digital Commons pages (Fairfield, New Haven) offering a public download of the
accepted manuscript while OpenAlex marks the location not free (is_oa false, version submittedVersion).
This sizes the pattern. No network. Run: python -m verification.crosscheck_digitalcommons
"""
import duckdb
from pipeline.config import DERIVED
con = duckdb.connect()
W = f"'{(DERIVED / 'works.parquet').as_posix()}'"
L = f"'{(DERIVED / 'work_locations.parquet').as_posix()}'"
DC = ("(l.landing_page_url like '%digitalcommons.%' or l.landing_page_url like '%elischolar.library.yale.edu%' "
      "or l.landing_page_url like '%/cgi/viewcontent.cgi%' or l.landing_page_url like '%scholarworks.%' "
      "or l.landing_page_url like '%repository.%.edu%' or l.landing_page_url like '%works.bepress.com%')")
SC = "w.in_scope and w.type in ('article','review') and w.publication_year between 2015 and 2025"
def show(t, q):
    print(f"\n### {t}\n"); print(con.execute(q).df().to_markdown(index=False))
show("Digital Commons-style repository locations (non-primary) on in-scope works: free or not, by host",
     f"""select regexp_extract(l.landing_page_url, 'https?://([^/]+)/', 1) host, count(*) locations,
         count(*) filter (where l.is_oa) free, round(100.0*count(*) filter (where l.is_oa)/count(*),1) pct_free
         from {L} l join {W} w using (work_id) where {SC} and not l.is_primary and {DC}
         and (l.landing_page_url like '%fairfield%' or l.landing_page_url like '%newhaven%' or l.landing_page_url like '%sacredheart%'
              or l.landing_page_url like '%elischolar%' or l.landing_page_url like '%wesleyan%' or l.landing_page_url like '%trincoll%'
              or l.landing_page_url like '%conncoll%' or l.landing_page_url like '%uconn%' or l.landing_page_url like '%quinnipiac%'
              or l.landing_page_url like '%southernct%' or l.landing_page_url like '%easternct%' or l.landing_page_url like '%wcsu%'
              or l.landing_page_url like '%ccsu%' or l.landing_page_url like '%usj%' or l.landing_page_url like '%bridgeport%'
              or l.landing_page_url like '%hartford%')
         group by 1 order by 2 desc""")
show("Same, all Digital Commons-style hosts together, by publication year band",
     f"""select case when w.publication_year<=2019 then '2015-2019' when w.publication_year<=2022 then '2020-2022' else '2023-2025' end band,
         count(*) locations, count(*) filter (where l.is_oa) free, round(100.0*count(*) filter (where l.is_oa)/count(*),1) pct_free
         from {L} l join {W} w using (work_id) where {SC} and not l.is_primary and l.landing_page_url like '%digitalcommons.%'
         group by 1 order by 1""")
show("In-scope CLOSED works (2015-2025) whose only repository evidence includes a not-free Digital Commons/EliScholar location",
     f"""select count(distinct w.work_id) works from {W} w join {L} l using (work_id) where {SC} and w.oa_status='closed'
         and not l.is_primary and (l.landing_page_url like '%digitalcommons.%' or l.landing_page_url like '%elischolar.library.yale.edu%')""")
show("Of those, by Connecticut repository host",
     f"""select regexp_extract(l.landing_page_url, 'https?://([^/]+)/', 1) host, count(distinct w.work_id) closed_works
         from {W} w join {L} l using (work_id) where {SC} and w.oa_status='closed' and not l.is_primary
         and (l.landing_page_url like '%digitalcommons.%' or l.landing_page_url like '%elischolar.library.yale.edu%')
         group by 1 order by 2 desc limit 12""")
show("Journal of Financial Crises (Yale, EliScholar) in-scope 2015-2025 by OA status",
     f"""select oa_status, count(*) n from {W} w where {SC} and source_name='Journal of Financial Crises' group by 1""")
