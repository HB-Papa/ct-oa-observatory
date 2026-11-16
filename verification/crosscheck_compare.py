"""Cross-check agent, part 1: agreement tables for the 510-article sample.

Reads only files already in data/derived/ (no network). Prints Markdown tables
used in docs/crosschecks.md and writes the disagreement lists to
verification/crosscheck_disagreements.csv for hand review.

Run from the project root:  python -m verification.crosscheck_compare
"""
from __future__ import annotations

import duckdb

from pipeline.config import DERIVED

C = DERIVED / "crosschecks"
con = duckdb.connect()
con.execute(f"create view s as select * from read_csv('{(C / 'sample.csv').as_posix()}', all_varchar=true)")
con.execute(f"create view u as select * from read_csv('{(C / 'unpaywall_sample.csv').as_posix()}', all_varchar=true)")
con.execute(f"create view o as select * from read_csv('{(C / 'openaire_sample.csv').as_posix()}', all_varchar=true)")
con.execute(f"create view loc as select * from '{(DERIVED / 'work_locations.parquet').as_posix()}'")
con.execute(f"create view w as select * from '{(DERIVED / 'works.parquet').as_posix()}'")
con.execute("""create table j as select s.institution_key, s.work_id, s.doi, s.year, s.oa_status, s.oa_category,
    lower(u.found) u_found, u.upw_oa_status, lower(u.upw_is_oa) upw_is_oa, lower(u.upw_has_repository_copy) upw_has_repository_copy,
    lower(o.found) o_found, o.oaire_access, o.oaire_color, lower(o.oaire_is_green) oaire_is_green, lower(o.oaire_in_diamond_journal) oaire_in_diamond_journal, o.oaire_n_records,
    coalesce((select bool_or(l.is_oa) from loc l where l.work_id=s.work_id and l.source_type='repository'), false) oa_repo,
    coalesce((select bool_or(l.is_oa) from loc l where l.work_id=s.work_id and l.source_type='repository'
              and l.source_id not in ('S2764455111','S4306400806')), false) oa_repo_non_pmc,
    coalesce((select bool_or(true) from loc l where l.work_id=s.work_id and l.source_type='repository'), false) any_repo
    from s left join u using (work_id) left join o using (work_id)""")


def show(title, sql):
    df = con.execute(sql).df()
    print(f"\n### {title}\n")
    print(df.to_markdown(index=False))
    return df


print("rows:", con.execute("select count(*) from j").fetchone())
show("OpenAlex oa_status counts", "select oa_status, count(*) n from j group by 1 order by 2 desc")
show("oa_category counts", "select oa_category, count(*) n from j group by 1 order by 2 desc")

# 1. Unpaywall
show("Unpaywall found", "select u_found, count(*) n from j group by 1")
show("OpenAlex oa_status vs Unpaywall oa_status (pivot)",
     """pivot (select oa_status, coalesce(upw_oa_status,'(not found)') upw from j) on upw using count(*) group by oa_status order by oa_status""")
show("Unpaywall exact agreement (diamond counted as gold)",
     """select count(*) filter (where u_found='true') found,
        count(*) filter (where u_found='true' and (upw_oa_status=oa_status or (oa_status='diamond' and upw_oa_status='gold'))) agree
        from j""")

# 2a. Free to read
show("OpenAIRE found / access label", "select o_found, coalesce(oaire_access,'(blank)') access, count(*) n from j group by 1,2 order by 1,2")
show("Free to read: OpenAlex vs OpenAIRE access",
     """pivot (select case when oa_status='closed' then 'OA closed' else 'OA free' end oa,
                       case when o_found<>'true' then '(not found)' else coalesce(oaire_access,'(blank)') end oaire from j)
        on oaire using count(*) group by oa order by oa""")
show("Free-to-read agreement where OpenAIRE gives OPEN/CLOSED/RESTRICTED/EMBARGO",
     """select count(*) compared,
        count(*) filter (where (oa_status<>'closed') = (oaire_access='OPEN')) agree,
        round(100.0*count(*) filter (where (oa_status<>'closed') = (oaire_access='OPEN'))/count(*),1) pct,
        count(*) filter (where oa_status='closed' and oaire_access='OPEN') oa_closed_oaire_open,
        count(*) filter (where oa_status<>'closed' and oaire_access<>'OPEN') oa_free_oaire_not_open
        from j where o_found='true' and oaire_access is not null""")
show("Free to read by OpenAlex status vs OpenAIRE",
     """pivot (select oa_status, case when o_found<>'true' then '(not found)' else coalesce(oaire_access,'(blank)') end oaire from j)
        on oaire using count(*) group by oa_status order by oa_status""")
show("Free-to-read agreement per institution (labelled OpenAIRE answers only)",
     """select institution_key, count(*) compared,
        count(*) filter (where (oa_status<>'closed') = (oaire_access='OPEN')) agree,
        round(100.0*count(*) filter (where (oa_status<>'closed') = (oaire_access='OPEN'))/count(*),1) pct,
        count(*) filter (where oa_status='closed' and oaire_access='OPEN') "OA closed / OAIRE open",
        count(*) filter (where oa_status<>'closed' and oaire_access<>'OPEN') "OA free / OAIRE not open",
        30-count(*) "not found or blank",
        round(100.0*count(*) filter (where oa_status<>'closed')/count(*),0) oa_free_pct,
        round(100.0*count(*) filter (where oaire_access='OPEN')/count(*),0) oaire_open_pct
        from j where o_found='true' and oaire_access is not null group by 1 order by 1""")
show("Free-to-read by year band",
     """select case when cast(year as int)<=2019 then '2015-2019' when cast(year as int)<=2022 then '2020-2022' else '2023-2025' end band,
        count(*) compared,
        round(100.0*count(*) filter (where (oa_status<>'closed') = (oaire_access='OPEN'))/count(*),1) pct_agree,
        count(*) filter (where oa_status='closed' and oaire_access='OPEN') oa_closed_oaire_open,
        count(*) filter (where oa_status<>'closed' and oaire_access<>'OPEN') oa_free_oaire_not_open
        from j where o_found='true' and oaire_access is not null group by 1 order by 1""")

# 2b. Publisher color
show("Publisher OA color: OpenAlex status vs OpenAIRE color",
     """pivot (select oa_status, case when o_found<>'true' then '(not found)' else coalesce(oaire_color,'(none)') end color from j)
        on color using count(*) group by oa_status order by oa_status""")
show("Color agreement (found in OpenAIRE; OpenAlex publisher color = gold/diamond->gold, hybrid, bronze, else none)",
     """with t as (select case when oa_status in ('gold','diamond') then 'gold' when oa_status in ('hybrid','bronze') then oa_status else '(none)' end a,
                         coalesce(oaire_color,'(none)') b from j where o_found='true')
        select count(*) compared, count(*) filter (where a=b) agree, round(100.0*count(*) filter (where a=b)/count(*),1) pct,
        count(*) filter (where a<>'(none)' and b<>'(none)') both_colored,
        count(*) filter (where a<>'(none)' and b<>'(none)' and a=b) both_colored_agree from t""")

# 2c. Repository copy
show("Repository copy: OpenAlex OA repository location vs OpenAIRE isGreen",
     """pivot (select case when oa_repo then 'OA repo copy' else 'no OA repo copy' end oa,
                       case when o_found<>'true' then '(not found)' when oaire_is_green='true' then 'isGreen true' else 'isGreen false' end oaire from j)
        on oaire using count(*) group by oa order by oa""")
show("Repo agreement (found)",
     """select count(*) compared, count(*) filter (where oa_repo = (oaire_is_green='true')) agree,
        round(100.0*count(*) filter (where oa_repo = (oaire_is_green='true'))/count(*),1) pct from j where o_found='true'""")
show("Repo copy restricted to non-PMC repositories vs isGreen",
     """pivot (select case when oa_repo_non_pmc then 'OA non-PMC repo' else 'no OA non-PMC repo' end oa,
                       case when oaire_is_green='true' then 'isGreen true' else 'isGreen false' end oaire from j where o_found='true')
        on oaire using count(*) group by oa order by oa""")
show("OpenAlex green status vs OpenAIRE isGreen",
     """pivot (select oa_status, case when o_found<>'true' then '(not found)' when oaire_is_green='true' then 'isGreen true' else 'isGreen false' end g from j)
        on g using count(*) group by oa_status order by oa_status""")
show("Diamond: OpenAlex diamond/oa_category vs OpenAIRE in diamond journal",
     """pivot (select oa_category, coalesce(oaire_in_diamond_journal,'(nf)') d from j) on d using count(*) group by oa_category""")

con.execute("""copy (select *, case
     when o_found='true' and oa_status='closed' and oaire_access='OPEN' then 'A_oa_closed_oaire_open'
     when o_found='true' and oa_status<>'closed' and oaire_access in ('CLOSED','RESTRICTED','EMBARGO') then 'B_oa_free_oaire_closed'
     when o_found='true' and oa_status='green' and oaire_is_green='false' then 'C_oa_green_oaire_not_green'
     when o_found='true' and oa_status<>'closed' and oaire_access is null then 'D_oa_free_oaire_blank'
     end grp from j where grp is not null order by grp, work_id) to 'verification/crosscheck_disagreements.csv' (header)""")
show("Disagreement groups", "select grp, count(*) n from read_csv('verification/crosscheck_disagreements.csv') group by 1 order by 1")
