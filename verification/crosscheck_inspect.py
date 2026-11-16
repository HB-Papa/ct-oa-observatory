"""Cross-check agent, part 2: side-by-side evidence for each disagreement.

Uses only cached responses (OpenAIRE and Unpaywall caches from s08/s09) and
works.parquet / work_locations.parquet. No network.

Writes verification/crosscheck_inspect_out.txt (one block per disagreement)
and prints a short tally of the OpenAIRE record sources for blank-access rows.

Run from the project root:  python -m verification.crosscheck_inspect
"""
from __future__ import annotations

import csv
import glob
import gzip
import json
from collections import Counter

import duckdb

from pipeline.config import DERIVED, RAW

def load_openaire() -> dict[str, list[dict]]:
    by_doi: dict[str, list[dict]] = {}
    for f in glob.glob(str(RAW / "openaire" / "*" / "*.json.gz")):
        body = json.loads(gzip.decompress(open(f, "rb").read()))["body"]
        for rec in body.get("results") or []:
            for p in rec.get("pids") or []:
                if p.get("scheme") == "doi":
                    by_doi.setdefault(p["value"].lower(), []).append(rec)
    return by_doi


def load_unpaywall() -> dict[str, dict]:
    out = {}
    for f in glob.glob(str(RAW / "unpaywall" / "*" / "*.json.gz")):
        body = json.loads(gzip.decompress(open(f, "rb").read()))["body"]
        if isinstance(body, dict) and body.get("doi"):
            out[body["doi"].lower()] = body
    return out


def main() -> None:
    oa = load_openaire()
    upw = load_unpaywall()
    con = duckdb.connect()
    locs = con.execute(f"""select work_id, source_name, source_type, version, is_oa, license, landing_page_url
        from '{(DERIVED / 'work_locations.parquet').as_posix()}' order by work_id, location_index""").fetchall()
    by_work: dict[str, list] = {}
    for l in locs:
        by_work.setdefault(l[0], []).append(l[1:])
    meta = {r[0]: r[1:] for r in con.execute(f"""select work_id, source_name, publisher_parent_name, primary_license, type
        from '{(DERIVED / 'works.parquet').as_posix()}'""").fetchall()}

    rows = list(csv.DictReader(open("verification/crosscheck_disagreements.csv", encoding="utf-8")))
    lines = []
    for r in rows:
        doi = r["doi"].lower()
        lines.append(f"\n==== {r['grp']} {r['work_id']} doi:{doi} year {r['year']} inst {r['institution_key']}")
        lines.append(f"  OpenAlex: {r['oa_status']} | journal {meta.get(r['work_id'])}")
        for l in by_work.get(r["work_id"], []):
            lines.append(f"    loc {l}")
        u = upw.get(doi)
        if u:
            b = u.get("best_oa_location") or {}
            lines.append(f"  Unpaywall: {u.get('oa_status')} best={b.get('host_type')} {b.get('version')} {b.get('url')}")
        for rec in oa.get(doi, []):
            lines.append(f"  OpenAIRE record {rec['id']} best={(rec.get('bestAccessRight') or {}).get('label')} "
                         f"color={rec.get('openAccessColor')} isGreen={rec.get('isGreen')} "
                         f"embargoEnd={rec.get('embargoEndDate')} date={rec.get('publicationDate')} "
                         f"from={[c['value'] for c in rec.get('collectedFrom') or []]}")
            for i in rec.get("instances") or []:
                lines.append(f"    inst {i.get('type')} | {(i.get('hostedBy') or {}).get('value')} | "
                             f"access={(i.get('accessRight') or {}).get('label')} oaRoute={(i.get('accessRight') or {}).get('openAccessRoute')} | "
                             f"lic={i.get('license')} | from={(i.get('collectedFrom') or {}).get('value')} | "
                             f"{(i.get('urls') or [''])[0]}")
    open("verification/crosscheck_inspect_out.txt", "w", encoding="utf-8").write("\n".join(lines))

    # Blank-access rows: where do their OpenAIRE records come from?
    sample = list(csv.DictReader(open(DERIVED / "crosschecks" / "openaire_sample.csv", encoding="utf-8")))
    st = {r["work_id"]: r for r in csv.DictReader(open(DERIVED / "crosschecks" / "sample.csv", encoding="utf-8"))}
    tally = Counter()
    for r in sample:
        if r["found"] == "True" and not r["oaire_access"]:
            srcs = {c["value"] for rec in oa.get(r["doi"].lower(), []) for c in rec.get("collectedFrom") or []}
            tally[(st[r["work_id"]]["oa_status"], "Crossref only" if srcs == {"Crossref"} else "other: " + "|".join(sorted(srcs)))] += 1
    for k, v in sorted(tally.items()):
        print(k, v)


if __name__ == "__main__":
    main()
