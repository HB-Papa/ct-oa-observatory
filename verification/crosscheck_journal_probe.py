"""Cross-check agent, part 4: probes of individual journals raised by the green proxy review.

No network. Run from the project root:  python -m verification.crosscheck_journal_probe
"""
import duckdb
from pipeline.config import DERIVED
con = duckdb.connect()
W = f"'{(DERIVED / 'works.parquet').as_posix()}'"
L = f"'{(DERIVED / 'work_locations.parquet').as_posix()}'"
SCOPE = "in_scope and type in ('article','review') and publication_year between 2015 and 2025"
def show(t, q):
    print(f"\n### {t}\n"); print(con.execute(q).df().to_markdown(index=False))
for j in ["Journal of Financial Crises", "International Journal of High Speed Electronics and Systems"]:
    show(f"{j}: OA status and source flags", f"""select oa_status, source_is_oa, source_is_in_doaj, count(*) n,
        min(publication_year) y0, max(publication_year) y1 from {W} where {SCOPE} and source_name='{j}' group by all""")
    show(f"{j}: sample landing pages", f"""select w.work_id, w.doi, l.landing_page_url, l.is_oa from {W} w join {L} l using (work_id)
        where w.in_scope and w.publication_year between 2015 and 2025 and w.source_name='{j}' and l.is_primary order by w.work_id limit 4""")
show("FASEB Journal closed/bronze 2015-2025: meeting-abstract supplements vs other",
     f"""select case when doi like '%supplement%' or doi like '%_supplement.%' then 'supplement (meeting abstract)' else 'other' end kind,
         count(*) n from {W} where {SCOPE} and source_name='The FASEB Journal' and oa_category in ('closed','bronze') group by 1""")
show("Blood closed/bronze 2015-2025 by DOI pattern (blood-YYYY-NNNNNN = ASH meeting abstract)",
     f"""select case when regexp_matches(doi, 'blood-20[0-9]{{2}}-[0-9]{{5,6}}$') then 'meeting abstract pattern' else 'other' end kind,
         oa_category, count(*) n from {W} where {SCOPE} and source_name='Blood' and oa_category in ('closed','bronze') group by all order by 1,2""")
show("Green proxy candidates (2015-2025) with meeting-abstract supplement DOIs",
     f"""select w.source_name, count(*) n from {W} w join read_csv('{(DERIVED / 'crosschecks' / 'green_proxy_journals.csv').as_posix()}') g using (source_id)
         where w.{SCOPE.replace(' and ', ' and w.', 1)} and w.oa_category in ('closed','bronze')
         and not coalesce(w.has_oa_accepted_repository_copy,false) and not coalesce(w.has_oa_published_repository_copy,false)
         and g.accepted_manuscript_repository_articles_2015_2025 >= 3 and (w.doi ilike '%supplement%' or w.doi ilike '%suppl%')
         group by rollup(w.source_name) order by n desc limit 8""")
show("Closed works 2015-2025 with supplement DOIs (statewide, distinct)",
     f"select count(*) from {W} where {SCOPE} and oa_category='closed' and (doi ilike '%supplement%' or doi ilike '%suppl%')")
