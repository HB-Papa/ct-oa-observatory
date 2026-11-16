"""Independent recomputation of Phase 3 metrics from the raw OpenAlex cache.

Reads only the raw cache (gzip JSON). Does not use the project pipeline.
Writes verification/mine.json with every figure.

Usage: python recompute.py [CACHE_DIR]
"""
import gzip
import json, os, re, sys, collections
from urllib.parse import parse_qs, urlparse

CACHE = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\chris\ct-oa-observatory-cache\openalex\2026-11-15"
HERE = os.path.dirname(os.path.abspath(__file__))

INST = {
    "yale": ["I32971472"], "uconn": ["I140172145", "I75929689"], "wesleyan": ["I100538780"],
    "trinity": ["I56722557"], "conncoll": ["I4498119"], "quinnipiac": ["I43267033"],
    "fairfield": ["I126350171"], "sacredheart": ["I130186095"], "hartford": ["I162281398"],
    "newhaven": ["I40253897"], "scsu": ["I35462925"], "ccsu": ["I154264771"],
    "wcsu": ["I204366597"], "ecsu": ["I203331390"], "uscga": ["I186274478"],
    "bridgeport": ["I154300980"], "usj": ["I192633058"],
}
ID2INST = {i: k for k, ids in INST.items() for i in ids}
# Diamond split (definition added 2026-11-16): "diamond" only when OpenAlex says diamond
# AND the recorded list fee is exactly 0; otherwise "oa_fee_unconfirmed". Both free to read.
STATUSES = ["diamond", "oa_fee_unconfirmed", "gold", "hybrid", "bronze", "green", "closed"]
FREE = {"diamond", "oa_fee_unconfirmed", "gold", "hybrid", "bronze", "green"}


def short(x):
    return x.rsplit("/", 1)[-1] if x else x


# ---------- load ----------
list_recs = {}          # id -> record (from list pages)
list_dupes = 0
single = {}             # id -> full record
for fn in sorted(os.listdir(CACHE)):
    if not fn.endswith(".json.gz"):
        continue
    with gzip.open(os.path.join(CACHE, fn), "rt", encoding="utf-8") as f:
        d = json.load(f)
    u, body = d["url"], d["body"]
    if "group_by=" in u or "/institutions" in u:
        continue
    # Only full harvest records: the select list must include authorships. (Other
    # cached queries, e.g. ID-only pages from later checks, are not harvest data.)
    sel = (parse_qs(urlparse(u).query).get("select") or [""])[0].split(",")
    if "authorships" not in sel:
        continue
    if u.startswith("https://api.openalex.org/works?") and "cursor=" in u and "select=" in u:
        for r in body.get("results", []):
            wid = short(r["id"])
            if wid in list_recs:
                list_dupes += 1
            list_recs[wid] = r
    elif re.match(r"https://api\.openalex\.org/works/W\d+\?", u):
        single[short(body["id"])] = body

# ---------- truncation handling ----------
trunc = [w for w, r in list_recs.items() if len(r.get("authorships") or []) >= 100]
missing_full = [w for w in trunc if w not in single]
replaced = 0
works = {}
for w, r in list_recs.items():
    if w in single and len(r.get("authorships") or []) >= 100:
        works[w] = single[w]
        replaced += 1
    else:
        works[w] = r
single_not_in_list = [w for w in single if w not in list_recs]


def insts_of_aff(inst):
    ids = [short(inst.get("id"))] + [short(x) for x in (inst.get("lineage") or [])]
    return {ID2INST[i] for i in ids if i in ID2INST}


def work_insts(r):
    s = set()
    for a in r.get("authorships") or []:
        for inst in a.get("institutions") or []:
            s |= insts_of_aff(inst)
    return s


def work_aff_map(r):
    """affiliation id -> set of our institutions, using the work's own lineage info."""
    m = collections.defaultdict(set)
    for a in r.get("authorships") or []:
        for inst in a.get("institutions") or []:
            m[short(inst.get("id"))] |= insts_of_aff(inst)
    return m


def corr_insts(r):
    m = work_aff_map(r)
    s = set()
    for c in r.get("corresponding_institution_ids") or []:
        c = short(c)
        if c in ID2INST:
            s.add(ID2INST[c])
        s |= m.get(c, set())
    return s


def publisher(r):
    src = ((r.get("primary_location") or {}).get("source")) or {}
    lin = src.get("host_organization_lineage_names") or []
    if lin:
        return lin[-1]
    return src.get("host_organization_name") or "Unknown"


def trinity_is_washington_college(r):
    """Definition added 2026-11-16 (double-check): OpenAlex matches authors at
    Washington College, Maryland, to Trinity College (whose founding name was
    Washington College). Drop the Trinity credit when the raw affiliation text of
    the authors matched to Trinity mentions "Washington College" and never "Trinity"."""
    texts = []
    for a in r.get("authorships") or []:
        if any("trinity" in insts_of_aff(i) for i in a.get("institutions") or []):
            texts += a.get("raw_affiliation_strings") or []
    low = [t.lower() for t in texts]
    return any("washington college" in t for t in low) and not any("trinity" in t for t in low)


def split_status(st, fee):
    if st != "diamond":
        return st
    return "diamond" if fee is not None and float(fee) == 0.0 else "oa_fee_unconfirmed"


# ---------- scope ----------
rows = []
excluded_A = collections.Counter()
excluded_trinity = collections.Counter()
excluded_abstract = collections.Counter()
# Meeting-abstract scope rule (Chris, 2026-11-16), restated here from the
# decision text rather than imported, so the check stays independent.
ABSTRACT_DOI = re.compile(
    r"10\.1212/wnl\..*_supplement|10\.1096/fasebj\..*_supplement|10\.1200/jco\..*_suppl"
    r"|10\.1161/[a-z]+\.[0-9]+\.suppl_|10\.1182/blood-20[0-9]{2}-[0-9]{5,6}$"
    r"|10\.1182/blood\.v[0-9]+\.2[23]\.[0-9]+\.[0-9]+$|10\.1254/jpssuppl\.|10\.1556/jba\.[0-9]+\.[0-9]+\.suppl", re.I)
out_of_scope = collections.Counter()
for w, r in works.items():
    y = r.get("publication_year")
    if r.get("type") not in ("article", "review") or not (2015 <= (y or 0) <= 2026):
        out_of_scope[(r.get("type"), y)] += 1
        continue
    src = ((r.get("primary_location") or {}).get("source")) or {}
    if src.get("type") == "repository" and not r.get("doi"):
        excluded_A[y] += 1
        continue
    if r.get("doi") and ABSTRACT_DOI.search(r["doi"]):
        excluded_abstract[y] += 1
        continue
    apc = (r.get("apc_list") or {}).get("value_usd")
    insts, corr = work_insts(r), corr_insts(r)
    if "trinity" in insts and trinity_is_washington_college(r):
        insts, corr = insts - {"trinity"}, corr - {"trinity"}
        if not insts:
            excluded_trinity[y] += 1
            continue
    rows.append(dict(
        id=w, year=y, status=split_status((r.get("open_access") or {}).get("oa_status"), apc),
        insts=insts, corr=corr,
        has_corr=bool(r.get("corresponding_institution_ids")),
        apc=apc, publisher=publisher(r),
    ))

no_inst = [x["id"] for x in rows if not x["insts"]]
C = [x for x in rows if 2015 <= x["year"] <= 2025]


def entity_rows(e, rs):
    if e == "statewide":
        return rs
    if e == "statewide_no_yale":
        return [x for x in rs if x["insts"] - {"yale"}]
    return [x for x in rs if e in x["insts"]]


ENTS = ["statewide", "statewide_no_yale"] + list(INST)
out = {"meta": dict(list_records=len(list_recs) + list_dupes, list_unique=len(list_recs),
                    list_dupes=list_dupes, single_records=len(single), truncated_in_list=len(trunc),
                    truncated_without_full=len(missing_full), replaced=replaced,
                    single_not_in_list=len(single_not_in_list),
                    out_of_scope=sum(out_of_scope.values()), in_scope_no_inst=len(no_inst),
                    in_scope_no_inst_sample=no_inst[:10])}

# 1
out["per_year"] = {y: sum(1 for x in rows if x["year"] == y) for y in range(2015, 2027)}
out["excluded_A"] = {"total": sum(excluded_A.values()), **{str(k): v for k, v in sorted(excluded_A.items())}}
out["excluded_meeting_abstracts"] = {"total": sum(excluded_abstract.values()), **{str(k): v for k, v in sorted(excluded_abstract.items())}}
out["excluded_trinity_correction"] = dict(sorted(excluded_trinity.items()))
# 2,3,4
out["works"] = {}
out["oa"] = {}
out["free_share"] = {}
for e in ENTS:
    rs = entity_rows(e, C)
    cnt = collections.Counter(x["status"] for x in rs)
    out["works"][e] = len(rs)
    out["oa"][e] = {s: cnt.get(s, 0) for s in STATUSES}
    out["oa"][e]["_other"] = sum(v for k, v in cnt.items() if k not in STATUSES)
    free = sum(cnt.get(s, 0) for s in FREE)
    out["free_share"][e] = {"free": free, "n": len(rs), "share": free / len(rs) if rs else None}
# 5
out["apc"] = {}
for e in ENTS:
    rs = [x for x in entity_rows(e, C) if x["status"] in ("gold", "hybrid")]
    if e == "statewide":
        corr = [x for x in rs if x["corr"]]
    elif e == "statewide_no_yale":
        corr = [x for x in rs if x["corr"] - {"yale"}]
    else:
        corr = [x for x in rs if e in x["corr"]]
    def s(lst):
        p = [x["apc"] for x in lst if x["apc"] is not None]
        return dict(works=len(lst), priced=len(p), usd=sum(p))
    out["apc"][e] = {"upper": s(rs), "corresponding": s(corr)}
# 6
out["corr_coverage"] = {e: (lambda rs: {"n": len(rs), "with": sum(x["has_corr"] for x in rs),
                                         "share": sum(x["has_corr"] for x in rs) / len(rs)})(entity_rows(e, C))
                        for e in ENTS}
# 7
pub = collections.defaultdict(lambda: [0, 0])
for x in C:
    pub[x["publisher"]][0] += 1
    pub[x["publisher"]][1] += x["status"] == "closed"
top = sorted(pub.items(), key=lambda kv: (-kv[1][1], kv[0]))[:10]
out["publishers_top"] = [{"publisher": k, "works": v[0], "closed": v[1]} for k, v in top]

with open(os.path.join(HERE, "mine.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, default=str)
print(json.dumps(out["meta"], indent=1))
print("per_year", out["per_year"]); print("excluded_A", out["excluded_A"])
