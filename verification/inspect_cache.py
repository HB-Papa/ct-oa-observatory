"""Quick inventory of the raw cache: classify files by URL kind."""
import gzip, json, os, sys, collections, re

CACHE = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\chris\ct-oa-observatory-cache\openalex\2026-11-15"
kinds = collections.Counter()
examples = {}
filters = collections.Counter()
for fn in os.listdir(CACHE):
    if not fn.endswith(".json.gz"):
        continue
    with gzip.open(os.path.join(CACHE, fn), "rt", encoding="utf-8") as f:
        d = json.load(f)
    u = d["url"]
    if "group_by=" in u or "/institutions" in u:
        k = "other"
    elif u.startswith("https://api.openalex.org/works?") and "cursor=" in u and "select=" in u:
        k = "list"
        m = re.search(r"filter=([^&]*)", u)
        filters[m.group(1) if m else None] += 1
    elif re.match(r"https://api\.openalex\.org/works/W\d+", u):
        k = "single"
    else:
        k = "unknown"
    kinds[k] += 1
    examples.setdefault(k, u)
print(kinds)
for k, v in examples.items():
    print(k, v[:400])
print("distinct list filters:", len(filters))
for f_, c in filters.most_common(40):
    print(c, f_[:300] if f_ else f_)
