"""Cross-check published OA status counts against OpenAlex group_by queries.

Route 1 (published): harvested records -> tidy tables -> metrics CSV.
Route 2 (this script): OpenAlex counts by oa_status directly
    = all works matching the filter
    - rule A works (primary location is a repository AND no DOI)
    - works removed by affiliation corrections (from the tables; 14 Trinity works)
About 6 credits per entity. Run: python verification/api_oa_crosscheck.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import duckdb, pandas as pd
from pipeline.institutions import INSTITUTIONS, ALL_IDS
from pipeline.openalex import get

BASE = "publication_year:2015-2025,type:article|review,is_retracted:false"
ENT = {"statewide": ALL_IDS, "bridgeport": ["I154300980"], "trinity": ["I56722557"],
       "sacredheart": ["I130186095"], "yale": ["I32971472"]}

def counts(f):
    b = get("works", {"filter": f, "group_by": "open_access.oa_status"}, "verify_api_oa_crosscheck")
    return {g["key"]: g["count"] for g in b["group_by"]}

con = duckdb.connect()
pub = pd.read_csv("data/derived/metrics/oa_status_2015_2025.csv")
rows = []
for ent, ids in ENT.items():
    f = f"authorships.institutions.lineage:{'|'.join(ids)},{BASE}"
    allc = counts(f)
    rulea = counts(f + ",primary_location.source.type:repository,has_doi:false")
    if ent == "statewide":
        corr_sql = """SELECT oa_status, COUNT(*) n FROM 'data/derived/works.parquet'
                      WHERE exclude_reason='affiliation_correction_no_ct_institution' AND publication_year<=2025 GROUP BY 1"""
    else:
        corr_sql = f"""SELECT w.oa_status, COUNT(*) n FROM 'data/derived/works.parquet' w
                      JOIN 'data/derived/work_institutions.parquet' wi USING (work_id)
                      WHERE wi.institution_key='{ent}' AND wi.affiliation_corrected
                        AND w.publication_year <= 2025 AND w.exclude_reason IS DISTINCT FROM 'repository_record_no_doi'
                      GROUP BY 1"""
    corr = dict(con.execute(corr_sql.replace("AND w.exclude_reason IS NULL\n", "AND w.exclude_reason IS NULL\n") ).fetchall())
    p = pub[pub.entity == ent].set_index("oa_status")["works"]
    for st in ["diamond", "gold", "hybrid", "bronze", "green", "closed"]:
        api = allc.get(st, 0) - rulea.get(st, 0) - corr.get(st, 0)
        rows.append({"entity": ent, "oa_status": st, "api_all": allc.get(st, 0), "minus_ruleA": rulea.get(st, 0),
                     "minus_corrections": corr.get(st, 0), "api_net": api, "published": int(p.get(st, 0)),
                     "diff": int(p.get(st, 0)) - api})
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).parent / "api_oa_crosscheck.csv", index=False)
print(df.to_string(index=False))
print("\nALL MATCH" if (df["diff"] == 0).all() else f"\nMISMATCHES: {(df['diff'] != 0).sum()}")
