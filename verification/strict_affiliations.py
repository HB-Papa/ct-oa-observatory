"""Strict affiliation check for all 17 institutions (2026-11-24).

Several of the institutions share names with other places or organizations
(Trinity College Dublin, Illinois Wesleyan, Hartford Hospital, Saint Joseph's
University in Philadelphia, and so on). The phase 3 check accepted any text
containing a short keyword, which these would pass. This check, for every
2015-2025 article and review OpenAlex credits to each institution, reads the
raw affiliation text of the authors OpenAlex matched to that institution and
classifies the credit:

- confirmed:   the text names the institution specifically (CONFIRM pattern)
- other:       the text names a different organization or place with a similar
               name (OTHER pattern) and nothing that confirms
- vague:       the text has the institution's keyword but too little to tell
- no_keyword:  the text exists but does not contain the keyword (typos,
               translations, department-only text)
- no_text:     OpenAlex has no raw affiliation text for those authors

Reads the saved 2026-11-15 harvest (the latest full harvest kept on this
computer). Prints counts per institution. Writes every non-confirmed credit to
verification/strict_affiliation_flags.csv for review by hand. That file holds
raw affiliation text and is kept out of git.

Usage: python verification/strict_affiliations.py [CACHE_DIR]
"""
import collections, csv, gzip, json, os, re, sys
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\chris\ct-oa-observatory-cache\openalex\2026-11-15"

# OpenAlex IDs (an institution and its lineage), same as pipeline/institutions.py
IDS = {
    "yale": ["I32971472"], "uconn": ["I140172145", "I75929689"], "wesleyan": ["I100538780"],
    "trinity": ["I56722557"], "conncoll": ["I4498119"], "quinnipiac": ["I43267033"],
    "fairfield": ["I126350171"], "sacredheart": ["I130186095"], "hartford": ["I162281398"],
    "newhaven": ["I40253897"], "scsu": ["I35462925"], "ccsu": ["I154264771"],
    "wcsu": ["I204366597"], "ecsu": ["I203331390"], "uscga": ["I186274478"],
    "bridgeport": ["I154300980"], "usj": ["I192633058"],
}
CT = r"(\bct\b|conn\.?\b|connecticut|06\d\d\d)"
RULES = {  # key: (keyword, CONFIRM, OTHER)
    "yale": (r"yale", r"yale(?![- ]?nus)", r"yale[- ]?nus"),
    "uconn": (r"connecticut|uconn", r"univ\w*\.?\s+(of\s+)?conn|uconn|connecticut health|storrs|farmington|conn(ecticut)?\s+univ",
              r"connecticut college|central connecticut|southern connecticut|western connecticut|eastern connecticut"),
    "wesleyan": (r"wesleyan", r"(?<!illinois )(?<!ohio )(?<!indiana )(?<!kansas )(?<!nebraska )(?<!texas )(?<!oklahoma )(?<!virginia )"
                 r"(?<!tennessee )(?<!southern )(?<!kentucky )(?<!iowa )(?<!dakota )(?<!houghton )wesleyan univ|middletown",
                 r"(illinois|ohio|indiana|kansas|nebraska|texas|oklahoma|virginia|tennessee|southern|kentucky|iowa|dakota|carolina|georgia|"
                 r"west virginia|houghton) wesleyan|wesleyan college|wesleyan school|wesleyan methodist"),
    "trinity": (r"trinity", r"trinity coll\w*[^|]{0,80}" + CT + r"|trinity coll\w*[^|]{0,40}hartford|hartford[^|]{0,40}trinity",
                r"dublin|ireland|trinity univ|san antonio|texas|trinity western|trinity christian|trinity international|"
                r"trinity washington|trinity college,?\s*(cambridge|oxford|melbourne|toronto)|cambridge|oxford|melbourne|toronto|"
                r"trinity health|trinity hospital|trinity school|trinity lutheran|trinity evangelical"),
    "conncoll": (r"connecticut college|conn\.? coll", r"connecticut college|conn\.? coll|new london",
                 r"univ\w*\.?\s+(of\s+)?connecticut|uconn|storrs"),
    "quinnipiac": (r"quinnipiac", r"quinnipiac", r"$^"),
    "fairfield": (r"fairfield", r"fairfield\s+univ|dolan\s+school|egan\s+school|fairfield[^|]{0,40}" + CT,
                  r"fairfield institute|fairfield,\s*(nj|new jersey|ia|iowa|oh|ohio|ca|california|al|tx|me|vt|mt|id)\b|maharishi|"
                  r"fairfield (medical|hospital)|nsw|sydney|australia"),
    "sacredheart": (r"sacred heart|sacro cuore|sacré", r"sacred heart univ\w*(?![^|]{0,40}(japan|tokyo|philippin|puerto|ital|rom|milan|korea|taiwan|uganda|lebanon))"
                    r"|sacred heart[^|]{0,60}fairfield",
                    r"sacro cuore|cattolica|catholic univ\w* of (the )?sacred heart|milan|rome|roma|italy|japan|tokyo|philippin|"
                    r"puerto rico|korea|taiwan|uganda|lebanon|sacred heart (hospital|medical|health|school|institute|children)|"
                    r"spokane|pensacola|oregon|eugene|chicago"),
    "hartford": (r"hartford|hartt|barney", r"univ\w*\.?\s+(of\s+)?hartford|hartt school|barney school|hillyer college|"
                 r"ward college|college of education, nursing and health professions",
                 r"hartford hospital|hartford healthcare|hartford health|connecticut children|trinity|saint francis|st\.? francis|"
                 r"institute of living|capital community|hartford public|hartford seminary|hartford international|hartford insurance|"
                 r"the hartford|hartford steam boiler"),
    "newhaven": (r"new haven|west haven", r"univ\w*\.?\s+(of\s+)?new haven|tagliatela|henry c\.? lee|pompea college",
                 r"yale|southern connecticut|albertus|gateway|veterans|\bva\b|haskins|hospital of saint raphael|saint raphael|"
                 r"new haven hospital|ynhh|connecticut agricultural"),
    "scsu": (r"southern connecticut|scsu|southern ct", r"southern connecticut|scsu|southern ct", r"$^"),
    "ccsu": (r"central connecticut|ccsu|central ct", r"central connecticut|ccsu|central ct", r"$^"),
    "wcsu": (r"western connecticut|wcsu|western ct", r"western connecticut state|wcsu|western ct", r"western connecticut health|danbury hospital|nuvance"),
    "ecsu": (r"eastern connecticut|ecsu|eastern ct", r"eastern connecticut|ecsu|eastern ct", r"$^"),
    "uscga": (r"coast guard|uscga", r"coast guard academy|uscga", r"research (and|&) development center|coast guard r&d"),
    "bridgeport": (r"bridgeport", r"univ\w*\.?\s+(of\s+)?bridgeport|\bub\b", r"bridgeport hospital|yale|st\.? vincent|bridgeport public"),
    "usj": (r"joseph", r"univ\w*\.?\s+(of\s+)?(saint|st\.?)\s*joseph(?!'s)[^|]{0,80}(" + CT[1:-1] + r"|west hartford|hartford)|"
            r"univ\w*\.?\s+(of\s+)?(saint|st\.?)\s*joseph,?\s*(west hartford|ct|connecticut)|saint joseph college[^|]{0,40}(" + CT[1:-1] + r"|hartford)|"
            r"university of saint joseph(?!'s)(?![^|]{0,60}(beirut|lebanon|maine|indiana|philadelphia|brooklyn|new york|macau|missouri))",
            r"joseph'?s univ|saint joseph's|st\.? joseph's|beirut|lebanon|liban|philadelphia|maine|indiana|brooklyn|macau|missouri|"
            r"(hospital|medical|health|mercy|regional|school)|université saint|universite saint|usj, beirut"),
}
COMP = {k: tuple(re.compile(p, re.I) for p in v) for k, v in RULES.items()}
ID2KEY = {i: k for k, ids in IDS.items() for i in ids}


def short(x):
    return x.rsplit("/", 1)[-1] if x else x


def keys_of(inst):
    ids = [short(inst.get("id"))] + [short(x) for x in inst.get("lineage") or []]
    return {ID2KEY[i] for i in ids if i in ID2KEY}


def load(cache):
    works, full = {}, {}
    for fn in os.listdir(cache):
        if not fn.endswith(".json.gz"):
            continue
        d = json.load(gzip.open(os.path.join(cache, fn), "rt", encoding="utf-8"))
        u, b = d["url"], d["body"]
        sel = (parse_qs(urlparse(u).query).get("select") or [""])[0].split(",")
        if "authorships" not in sel or "group_by" in u:
            continue
        if "/works?" in u and "cursor=" in u:
            for r in b.get("results", []):
                works[r["id"]] = r
        elif re.search(r"/works/W\d+\?", u):
            full[b["id"]] = b
    return works, full


def classify(key, texts):
    kw, confirm, other = COMP[key]
    if not texts:
        return "no_text"
    if any(confirm.search(t) for t in texts):
        return "confirmed"
    if any(other.search(t) for t in texts):
        return "other"
    if any(kw.search(t) for t in texts):
        return "vague"
    return "no_keyword"


def credits(works, full):
    """Yield (work_id, year, key, matched-author texts, record) for each credit."""
    for wid, r in works.items():
        if not (2015 <= (r.get("publication_year") or 0) <= 2025) or r.get("type") not in ("article", "review"):
            continue
        if len(r.get("authorships") or []) >= 100 and wid in full:
            r = full[wid]
        per = collections.defaultdict(list)
        for a in r.get("authorships") or []:
            ks = set().union(*[keys_of(i) for i in a.get("institutions") or []]) if a.get("institutions") else set()
            for k in ks:
                per[k] += a.get("raw_affiliation_strings") or []
        for k, texts in per.items():
            yield short(wid), r.get("publication_year"), k, texts, r


def main():
    works, full = load(CACHE)
    counts = collections.defaultdict(collections.Counter)
    flags = []
    for wid, year, k, texts, r in credits(works, full):
        c = classify(k, texts)
        counts[k][c] += 1
        if c != "confirmed":
            src = ((r.get("primary_location") or {}).get("source") or {}).get("display_name")
            flags.append({"institution": k, "class": c, "work_id": wid, "year": year, "journal": src,
                          "affiliation_text": " | ".join(sorted(set(texts)))[:400]})
    print(f"{'institution':12} {'credits':>7} {'confirmed':>9} {'other':>6} {'vague':>6} {'no_kw':>6} {'no_text':>7}")
    for k in IDS:
        c = counts[k]; t = sum(c.values())
        print(f"{k:12} {t:7} {c['confirmed']/t:9.1%} {c['other']:6} {c['vague']:6} {c['no_keyword']:6} {c['no_text']:7}")
    with open(os.path.join(HERE, "strict_affiliation_flags.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["institution", "class", "work_id", "year", "journal", "affiliation_text"])
        w.writeheader()
        w.writerows(sorted(flags, key=lambda x: (x["institution"], x["class"], x["year"])))


if __name__ == "__main__":
    main()
