"""Sanity checks: (1) effect of the 100-author truncation, (2) why Bridgeport's free share is high.
Also tests alternative no-Yale corresponding definitions. Reuses recompute.py in-process."""
import runpy, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
g = runpy.run_path(os.path.join(HERE, "recompute.py"))
C, list_recs, single, work_insts, works = g["C"], g["list_recs"], g["single"], g["work_insts"], g["works"]

# (1) truncation impact on institution membership
changed = collections.Counter()
for w in single:
    a, b = work_insts(list_recs[w]), work_insts(single[w])
    for i in b - a:
        changed[i] += 1
print("works gaining an institution once full author list is used:", dict(changed))

# (2) Bridgeport: free share drivers
br = [x for x in C if "bridgeport" in x["insts"]]
pub = collections.Counter(x["publisher"] for x in br)
print("bridgeport top publishers:", pub.most_common(6))
src = collections.Counter()
for x in br:
    s = ((works[x["id"]].get("primary_location") or {}).get("source") or {})
    if x["status"] in ("diamond", "gold"):
        src[(s.get("display_name"), x["status"])] += 1
print("bridgeport top diamond/gold sources:", src.most_common(8))
unk = [x for x in br if x["publisher"] == "Unknown"]
print("bridgeport Unknown-publisher works by status:", collections.Counter(x["status"] for x in unk))
print("bridgeport works by year:", sorted(collections.Counter(x["year"] for x in br).items()))

# (3) alternative no-Yale corresponding definitions
gh = [x for x in C if x["status"] in ("gold", "hybrid") and x["insts"] - {"yale"}]
def s(lst):
    p = [x["apc"] for x in lst if x["apc"] is not None]
    return len(lst), len(p), sum(p)
print("noYale A (non-Yale inst corresponding):", s([x for x in gh if x["corr"] - {"yale"}]))
print("noYale B (any of 17 corresponding):    ", s([x for x in gh if x["corr"]]))
print("noYale B-A (Yale the only CT corresp.):", s([x for x in gh if x["corr"] == {"yale"}]))
