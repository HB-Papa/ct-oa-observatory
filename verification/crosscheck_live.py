"""Cross-check agent, part 5: a small number of live checks (under 150 requests).

1. Current OpenAlex record for selected works (single-record lookups, 0 credits).
   The API key is read from .env and sent as a header. It is never printed or saved.
2. Landing pages for selected URLs: HTTP status, final URL, and whether the page
   text contains common "free full text" or "paywall" phrases.

Results go to verification/crosscheck_live_out.json (no key, no email).

Run from the project root:  python -m verification.crosscheck_live
"""
from __future__ import annotations

import json
import os
import re
import time

import requests
from dotenv import load_dotenv

from pipeline.config import ROOT

load_dotenv(ROOT / ".env")
KEY = os.getenv("OPENALEX_API_KEY", "").strip()
UA = {"User-Agent": "Mozilla/5.0 (compatible; oa-crosscheck/1.0)"}

WORKS = [
    # group A: OpenAlex closed, OpenAIRE open
    "W2183917196", "W2442085864", "W2998909943", "W2733628627", "W2763826390", "W2952739627",
    "W4388484113", "W3095231685", "W3174498221", "W2900793605", "W2944866439", "W4286715683",
    "W2395577023", "W4404196319",
    # group B: OpenAlex free, OpenAIRE closed
    "W4386481910", "W4283324890", "W3016286018", "W2802843565", "W4200118937", "W7204186396",
    "W4296619485", "W3217125567",
    # green proxy / other probes
    "W2954967843", "W2576203379", "W2529055067",
]
PAGES = {
    "W2183917196 Fairfield DC": "https://digitalcommons.fairfield.edu/chemistry-facultypubs/42",
    "W2442085864 New Haven DC": "https://digitalcommons.newhaven.edu/economics-facpubs/9",
    "W2998909943 Fairfield DC": "https://digitalcommons.fairfield.edu/nursing-facultypubs/235",
    "W2733628627 JCTP DOI": "https://doi.org/10.31274/jctp-180810-73",
    "W2954967843 J Financial Crises DOI": "https://doi.org/10.17132/2693-3179.1011",
    "W3095231685 Blood abstract DOI": "https://doi.org/10.1182/blood-2020-134718",
    "W2900793605 Unpaywall-era PDF": "http://pau.go.ug/uploads/NATIONAL_LOCAL_CONTENT_POLICY_FOR_PETROLEUM_IN_UGANDA.pdf",
    "W2952739627 Gerontologist DOI": "https://doi.org/10.1093/geront/gnz083",
    "W4388484113 Int Affairs DOI": "https://doi.org/10.1093/ia/iiad249",
    "W2763826390 Inderscience DOI": "https://doi.org/10.1504/ijmrs.2017.087371",
    "W2802843565 Elsevier AAM": "https://www.sciencedirect.com/science/article/am/pii/S0889974616304546",
    "W7204186396 EMRO DOI": "https://doi.org/10.59236/emro.v3i7a1315",
    "W2576203379 PNAS DOI": "https://doi.org/10.1073/pnas.1613422114",
    "W3217125567 SAGE DOI": "https://doi.org/10.1177/02662426211020608",
}
FREE = ["download pdf", "full text", "viewcontent.cgi", "open access", "free access", "creative commons",
        "citation_pdf_url", "download", "free to read"]
PAY = ["purchase", "buy article", "access through your institution", "get access", "subscribe",
       "rent this article", "sign in to access"]


def work(wid: str) -> dict:
    r = requests.get(f"https://api.openalex.org/works/{wid}",
                     params={"select": "id,doi,open_access,best_oa_location,locations,primary_location"},
                     headers={"Authorization": f"Bearer {KEY}"} | UA, timeout=60)
    if r.status_code != 200:
        return {"status": r.status_code}
    b = r.json()
    return {"oa_status": b["open_access"]["oa_status"], "oa_url": b["open_access"].get("oa_url"),
            "locations": [{"source": (l.get("source") or {}).get("display_name"), "is_oa": l.get("is_oa"),
                           "version": l.get("version"), "pdf_url": l.get("pdf_url"),
                           "landing": l.get("landing_page_url")} for l in b.get("locations") or []]}


def page(url: str) -> dict:
    try:
        r = requests.get(url, headers=UA, timeout=40, allow_redirects=True)
    except requests.RequestException as e:
        return {"error": type(e).__name__}
    text = r.text.lower() if "text" in r.headers.get("content-type", "") else ""
    out = {"status": r.status_code, "final_url": r.url, "content_type": r.headers.get("content-type"),
           "bytes": len(r.content),
           "free_phrases": [p for p in FREE if p in text], "paywall_phrases": [p for p in PAY if p in text]}
    m = re.search(r'<meta name="citation_pdf_url" content="([^"]+)"', r.text) if text else None
    if m:
        out["citation_pdf_url"] = m.group(1)
    # Page titles are not stored: repository titles include author names.
    return out


def main() -> None:
    res = {"openalex": {}, "pages": {}}
    for w in WORKS:
        res["openalex"][w] = work(w)
        time.sleep(0.2)
    for k, u in PAGES.items():
        res["pages"][k] = page(u)
        time.sleep(0.5)
    json.dump(res, open("verification/crosscheck_live_out.json", "w", encoding="utf-8"), indent=1)
    print("requests:", len(WORKS) + len(PAGES))


if __name__ == "__main__":
    main()
