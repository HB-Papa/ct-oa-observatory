"""Strict affiliation check for Fairfield University (2026-11-24).

"Fairfield" is a common place name, so a match on the word alone is not
enough. For every 2015-2025 article and review OpenAlex credits to Fairfield
University (I126350171), this reads the raw affiliation text of the authors
OpenAlex matched to Fairfield and classifies the article:
- confirmed:    names Fairfield University, one of its schools, or Fairfield
                together with Connecticut, CT or the 06824/06825 ZIP codes
- other_place:  mentions a different Fairfield (Iowa, Ohio, New Jersey,
                California, Australia, a hospital) and nothing that confirms
- vague:        just "Fairfield" with nothing to say which one
- no_text:      OpenAlex has no raw affiliation text for those authors
Reads the saved 2026-11-15 harvest. Counts are printed; examples of anything
not confirmed go to verification/fairfield_affiliation_flags.csv (journal and
affiliation text only, no author names).
"""
import collections, csv, gzip, json, os, re, sys
from urllib.parse import parse_qs, urlparse

CACHE = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\chris\ct-oa-observatory-cache\openalex\2026-11-15"
FU = "I126350171"
CONFIRM = re.compile(r"fairfield\s+univ|dolan\s+school|egan\s+school|marion\s+peckham|school\s+of\s+engineering.*fairfield"
                     r"|fairfield[^;]{0,40}\b(ct|conn\.?|connecticut)\b|0682[45]", re.I)
OTHER = re.compile(r"iowa|\bia\b|maharishi|ohio|\boh\b|new jersey|\bnj\b|california|\bca\b|australia|nsw|sydney|liverpool"
                   r"|medical cent|hospital|alabama|\bal\b|texas|\btx\b|illinois|maine|vermont|montana|idaho|pennsylvania|uk\b|england", re.I)

works, full = {}, {}
for fn in os.listdir(CACHE):
    if not fn.endswith(".json.gz"):
        continue
    d = json.load(gzip.open(os.path.join(CACHE, fn), "rt", encoding="utf-8"))
    u, b = d["url"], d["body"]
    # Only harvest pages: the select list itself must include authorships (other
    # saved queries mention authorships in their filter but fetch IDs only).
    sel = (parse_qs(urlparse(u).query).get("select") or [""])[0].split(",")
    if "authorships" not in sel or "group_by" in u:
        continue
    if "/works?" in u and "cursor=" in u:
        for r in b.get("results", []):
            works[r["id"]] = r
    elif re.search(r"/works/W\d+\?", u):
        full[b["id"]] = b

def lineage_hit(inst):
    return FU in (inst.get("id") or "") or any(FU in x for x in inst.get("lineage") or [])

counts, flags = collections.Counter(), []
for wid, r in works.items():
    if not (2015 <= (r.get("publication_year") or 0) <= 2025) or r.get("type") not in ("article", "review"):
        continue
    if len(r.get("authorships") or []) >= 100 and wid in full:
        r = full[wid]
    texts = [s for a in r.get("authorships") or [] if any(lineage_hit(i) for i in a.get("institutions") or [])
             for s in a.get("raw_affiliation_strings") or []]
    if not any(lineage_hit(i) for a in r.get("authorships") or [] for i in a.get("institutions") or []):
        continue
    if not texts:
        c = "no_text"
    elif any(CONFIRM.search(t) for t in texts):
        c = "confirmed"
    elif any("fairfield" in t.lower() and OTHER.search(t) for t in texts):
        c = "other_place"
    elif any("fairfield" in t.lower() for t in texts):
        c = "vague"
    else:
        c = "no_fairfield_in_text"
    counts[c] += 1
    if c not in ("confirmed",):
        src = ((r.get("primary_location") or {}).get("source") or {}).get("display_name")
        flags.append({"work_id": wid.split("/")[-1], "year": r.get("publication_year"), "class": c, "journal": src,
                      "affiliation_text": " | ".join(sorted(set(texts)))[:300]})

total = sum(counts.values())
print("Fairfield articles 2015-2025 in the harvest:", total)
for k, v in counts.most_common():
    print(f"  {k}: {v} ({v / total:.1%})")
with open(os.path.join(os.path.dirname(__file__), "fairfield_affiliation_flags.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["work_id", "year", "class", "journal", "affiliation_text"])
    w.writeheader(); w.writerows(sorted(flags, key=lambda x: x["class"]))
