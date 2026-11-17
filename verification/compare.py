"""Compare verification/mine.json with the published CSVs in data/derived/metrics.

Writes verification/comparison.json and prints a summary. Run after recompute.py.
"""
import json, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
MET = os.path.join(HERE, "..", "data", "derived", "metrics")
mine = json.load(open(os.path.join(HERE, "mine.json"), encoding="utf-8"))
res = {}


def rec(fig, key, m, p, tol):
    d = None if (m is None or p is None) else m - p
    ok = d is not None and abs(d) <= tol
    res.setdefault(fig, []).append(dict(key=key, mine=m, published=p, diff=d, ok=ok))


# 1 per-year totals (statewide) from by-year file
fy = pd.read_csv(os.path.join(MET, "free_to_read_by_year.csv"))
oy = pd.read_csv(os.path.join(MET, "oa_category_by_year.csv"))
for y in range(2015, 2027):
    p = fy[(fy.entity == "statewide") & (fy.publication_year == y)].works
    rec("1_per_year", str(y), mine["per_year"][str(y)], int(p.iloc[0]) if len(p) else None, 0)
    p2 = oy[(oy.entity == "statewide") & (oy.publication_year == y)].works.sum()
    rec("1_per_year_oa_file", str(y), mine["per_year"][str(y)], int(p2), 0)

# 2 & 4
ft = pd.read_csv(os.path.join(MET, "free_to_read_2015_2025.csv")).set_index("entity")
for e, v in mine["free_share"].items():
    rec("2_works", e, v["n"], int(ft.loc[e, "works"]) if e in ft.index else None, 0)
    rec("4_free_count", e, v["free"], int(ft.loc[e, "free_to_read"]) if e in ft.index else None, 0)
    rec("4_free_share", e, v["share"], float(ft.loc[e, "free_to_read_share"]) if e in ft.index else None, 0.001)

# 3
oa = pd.read_csv(os.path.join(MET, "oa_category_2015_2025.csv"))
for e in ["statewide", "statewide_no_yale", "bridgeport", "yale", "trinity"]:
    for s in ["diamond", "oa_fee_unconfirmed", "gold", "hybrid", "bronze", "green", "closed"]:
        p = oa[(oa.entity == e) & (oa.oa_category == s)].works
        rec("3_oa_status", f"{e}/{s}", mine["oa"][e][s], int(p.iloc[0]) if len(p) else None, 0)

# 5
ap = pd.read_csv(os.path.join(MET, "apc_estimates_2015_2025.csv"))
meth = {"upper": "upper_bound_all_authors", "corresponding": "corresponding_author"}
for e in ["statewide", "statewide_no_yale", "yale", "uconn", "quinnipiac", "bridgeport"]:
    for k, m in meth.items():
        r = ap[(ap.entity == e) & (ap.method == m)].iloc[0]
        v = mine["apc"][e][k]
        rec("5_apc_works", f"{e}/{k}", v["works"], int(r.paid_oa_works), 0)
        rec("5_apc_priced", f"{e}/{k}", v["priced"], int(r.works_with_list_price), 0)
        rec("5_apc_usd", f"{e}/{k}", v["usd"], float(r.estimated_usd), 1)

# 6
cc = pd.read_csv(os.path.join(MET, "corresponding_coverage.csv"))
cc = cc[cc.period == "complete"].set_index("entity")
for e, v in mine["corr_coverage"].items():
    rec("6_corr_with", e, v["with"], int(cc.loc[e, "with_corresponding_info"]), 0)
    rec("6_corr_share", e, v["share"], float(cc.loc[e, "coverage_share"]), 0.001)

# 7
pb = pd.read_csv(os.path.join(MET, "publishers_2015_2025.csv"))
pb = pb[pb.entity == "statewide"].sort_values("rank_by_closed")
top_pub = pb.head(5).reset_index(drop=True)
for i, t in enumerate(mine["publishers_top"][:5]):
    pr = top_pub.iloc[i]
    rec("7_publishers", f"rank{i+1} name: {t['publisher']} | {pr.publisher_parent_name}",
        int(t["publisher"] == pr.publisher_parent_name), 1, 0)
    rec("7_publishers", f"rank{i+1} works", t["works"], int(pr.works), 0)
    rec("7_publishers", f"rank{i+1} closed", t["closed"], int(pr.closed), 0)

json.dump(res, open(os.path.join(HERE, "comparison.json"), "w"), indent=1, default=float)
for fig, lst in res.items():
    bad = [x for x in lst if not x["ok"]]
    print(f"{fig}: {'PASS' if not bad else 'FAIL'} ({len(lst)-len(bad)}/{len(lst)})")
    for b in bad:
        print("   ", b)
print(top_pub[["publisher_parent_name", "works", "closed"]])
print(mine["publishers_top"][:6])

# Exit with an error if any figure group failed, so an automated refresh stops.
if any(not x["ok"] for lst in res.values() for x in lst):
    raise SystemExit(1)
