"""Affiliation accuracy check (phase 3 double-check, 2026-11-16).

For every in-scope work credited to an institution, look at the raw
affiliation text of the authors OpenAlex matched to that institution.
- confirmed:  at least one of those authors' raw strings names the institution
- no_text:    OpenAlex has no raw affiliation string for those authors
- unconfirmed: raw strings exist but none names the institution (possible
              affiliation error by OpenAlex)
Writes verification/affiliation_check.csv (counts only, safe to publish) and
verification/affiliation_unconfirmed_samples.csv (raw affiliation text, which
can include researchers' names and emails: kept local by .gitignore, never published).
"""
import collections, csv, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from pipeline.institutions import INSTITUTIONS
from pipeline.s03_harvest_works import pages, YEARS
from pipeline.s03b_fetch_full_authorships import full_record, AUTHOR_CAP
from pipeline.s04_build_tables import exclude_reason

PAT = {"yale": r"yale", "uconn": r"connecticut|uconn|storrs|farmington", "wesleyan": r"wesleyan",
       "trinity": r"trinity", "conncoll": r"connecticut college|conn\.? coll", "quinnipiac": r"quinnipiac",
       "fairfield": r"fairfield", "sacredheart": r"sacred heart", "hartford": r"hartford",
       "newhaven": r"new haven|west haven", "scsu": r"southern connecticut|scsu",
       "ccsu": r"central connecticut|ccsu", "wcsu": r"western connecticut|wcsu",
       "ecsu": r"eastern connecticut|ecsu", "uscga": r"coast guard", "bridgeport": r"bridgeport",
       "usj": r"s(ain)?t\.? joseph"}
ID2KEY = {i: k for k, _, ids, _ in INSTITUTIONS for i in ids}
short = lambda x: x.rsplit("/", 1)[-1]

status = collections.Counter(); samples = collections.defaultdict(list)
for year in YEARS:
    for body in pages(year):
        for w in body["results"]:
            if len(w["authorships"]) >= AUTHOR_CAP:
                w = full_record(short(w["id"]))
            src = ((w.get("primary_location") or {}).get("source") or {})
            if exclude_reason(src.get("type") == "repository", w.get("doi")):
                continue
            per_inst = collections.defaultdict(list)  # key -> raw strings of matched authors
            for a in w["authorships"]:
                for inst in a["institutions"]:
                    ids = {short(inst["id"])} | {short(l) for l in inst.get("lineage") or []}
                    for k in {ID2KEY[i] for i in ids if i in ID2KEY}:
                        per_inst[k] += a.get("raw_affiliation_strings") or []
            for k, strs in per_inst.items():
                if not strs: s = "no_text"
                elif any(re.search(PAT[k], x, re.I) for x in strs): s = "confirmed"
                else:
                    s = "unconfirmed"
                    if len(samples[k]) < 400: samples[k].append((w["publication_year"], short(w["id"]), " | ".join(strs)[:200]))
                status[(k, w["publication_year"] <= 2025, s)] += 1

rows = []
for k, *_ in INSTITUTIONS:
    for complete in (True,):
        c = {s: status[(k, complete, s)] for s in ("confirmed", "no_text", "unconfirmed")}
        tot = sum(c.values())
        rows.append({"institution_key": k, "works_2015_2025": tot, **c,
                     "pct_confirmed": round(100 * c["confirmed"] / tot, 1),
                     "pct_unconfirmed": round(100 * c["unconfirmed"] / tot, 1)})
df = pd.DataFrame(rows).sort_values("pct_unconfirmed", ascending=False)
here = Path(__file__).parent
df.to_csv(here / "affiliation_check.csv", index=False)
with open(here / "affiliation_unconfirmed_samples.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f); wr.writerow(["institution_key", "year", "work_id", "raw_strings_of_matched_authors"])
    for k, v in samples.items():
        for r in v: wr.writerow([k, *r])
print(df.to_string(index=False))
