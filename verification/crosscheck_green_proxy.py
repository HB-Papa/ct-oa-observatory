"""Cross-check agent, part 3: sanity checks on the green OA proxy (s12).

No network. Re-applies the s12 candidate rule to works.parquet and asks:
- do any candidates already have a free copy outside the publisher (a free
  repository copy of any version, or a free non-primary location that OpenAlex
  files under a journal or no source at all)?
- how is "Journal of Media Literacy Education" being used as a location source
  (it appears as the source of University of Rhode Island repository copies)?
- which large journals are flagged / not flagged, for a plausibility review.

Run from the project root:  python -m verification.crosscheck_green_proxy
"""
from __future__ import annotations

import duckdb

from pipeline.config import DERIVED

con = duckdb.connect()
W = f"'{(DERIVED / 'works.parquet').as_posix()}'"
L = f"'{(DERIVED / 'work_locations.parquet').as_posix()}'"
G = f"'{(DERIVED / 'crosschecks' / 'green_proxy_journals.csv').as_posix()}'"
con.execute(f"create view ev as select source_id, accepted_manuscript_repository_articles_2015_2025 n, shows_deposit_evidence flag from read_csv({G})")
con.execute(f"""create table cand as select w.* , ev.n from {W} w join ev using (source_id)
    where w.in_scope and w.type in ('article','review') and w.publication_year between 2015 and 2025
    and w.oa_category in ('closed','bronze') and not coalesce(w.has_oa_accepted_repository_copy,false)
    and not coalesce(w.has_oa_published_repository_copy,false) and ev.n >= 3""")


def show(title, sql):
    print(f"\n### {title}\n")
    print(con.execute(sql).df().to_markdown(index=False))


show("Candidates (distinct works, 2015-2025) by category", "select oa_category, count(*) n from cand group by 1")
show("Closed works (all in scope) that still have any free location (should be 0)",
     f"""select count(distinct w.work_id) n from {W} w join {L} l using (work_id)
         where w.in_scope and w.oa_status='closed' and l.is_oa""")
show("Candidates with a free non-primary location, by kind",
     f"""select c.oa_category,
         case when l.source_type='repository' then 'repository, ' || coalesce(l.version,'no version')
              when l.source_type is null then 'no source (e.g. preprint server DOI), ' || coalesce(l.version,'no version')
              else coalesce(l.source_type,'?') || ' typed, ' || coalesce(l.version,'no version') end kind,
         count(distinct c.work_id) works
         from cand c join {L} l using (work_id) where l.is_oa and not l.is_primary group by all order by 1, 3 desc""")
show("Candidates with ANY free non-primary location (distinct works)",
     f"""select count(distinct c.work_id) works from cand c join {L} l using (work_id) where l.is_oa and not l.is_primary""")
show("Top repositories hosting free submitted-version copies of candidates",
     f"""select l.source_name, count(distinct c.work_id) works from cand c join {L} l using (work_id)
         where l.is_oa and not l.is_primary and l.source_type='repository' group by 1 order by 2 desc limit 8""")
show("'Journal of Media Literacy Education' locations: where do they point?",
     f"""select case when l.landing_page_url like '%digitalcommons.uri.edu/jmle%' then 'JMLE article itself'
                     when l.landing_page_url like '%digitalcommons.uri.edu%' then 'other URI Digital Commons paper'
                     else 'elsewhere' end target, l.is_primary, count(distinct l.work_id) works
         from {L} l where l.source_name='Journal of Media Literacy Education' group by all order by 3 desc""")
show("Non-primary free locations typed as 'journal' whose source differs from the primary source (all in-scope works)",
     f"""select l.source_name, count(distinct l.work_id) works from {L} l join {W} w using (work_id)
         where w.in_scope and not l.is_primary and l.is_oa and l.source_type='journal' and l.source_id <> w.source_id
         group by 1 order by 2 desc limit 10""")
show("Flagged journals with most Connecticut candidates",
     """select source_name journal, any_value(publisher_parent_name) publisher, any_value(n) evidence_articles,
        count(*) ct_candidates from cand group by 1 order by 4 desc limit 15""")
show("Largest not-flagged journals by Connecticut closed+bronze works",
     f"""select w.source_name journal, any_value(w.publisher_parent_name) publisher, any_value(ev.n) evidence_articles,
         count(*) ct_closed_or_bronze from {W} w join ev using (source_id)
         where w.in_scope and w.type in ('article','review') and w.publication_year between 2015 and 2025
         and w.oa_category in ('closed','bronze') and ev.n < 3 group by 1 order by 4 desc limit 15""")
show("Flag rate by publisher (journals with any CT closed/bronze work; top publishers)",
     f"""with jp as (select distinct w.source_id, w.publisher_parent_name p from {W} w where w.in_scope)
         select p publisher, count(*) journals, sum(case when ev.flag then 1 else 0 end) flagged,
         round(100.0*sum(case when ev.flag then 1 else 0 end)/count(*),0) pct
         from ev join jp using (source_id) group by 1 order by 2 desc limit 12""")
show("Where the most common mis-typed 'journal' locations point (host of landing page)",
     f"""select l.source_name, regexp_extract(l.landing_page_url, 'https?://([^/]+)/', 1) host, l.version, count(distinct l.work_id) works
         from {L} l join {W} w using (work_id) where w.in_scope and not l.is_primary and l.is_oa and l.source_type='journal'
         and l.source_id <> w.source_id and l.source_name in ('ENLIGHTEN (Jurnal Bimbingan dan Konseling Islam)','Työväentutkimus Vuosikirja',
         'Socio-Environmental Systems Modeling','Civil War Book Review','Journal of Media Literacy Education','The Medicine Forum')
         group by all order by works desc limit 10""")
