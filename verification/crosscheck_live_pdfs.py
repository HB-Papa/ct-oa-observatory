"""Cross-check agent, part 5b: do the repository PDFs behind group-A disagreements open?

Fetches 4 Digital Commons PDF links (and the JFC landing page to find its PDF link).
Writes verification/crosscheck_live_pdfs_out.json. Run: python -m verification.crosscheck_live_pdfs
"""
import json, re, time
import requests
UA = {"User-Agent": "Mozilla/5.0 (compatible; oa-crosscheck/1.0)"}
URLS = {
 "W2183917196": "https://digitalcommons.fairfield.edu/cgi/viewcontent.cgi?article=1041&context=chemistry-facultypubs",
 "W2442085864": "https://digitalcommons.newhaven.edu/cgi/viewcontent.cgi?article=1008&context=economics-facpubs",
 "W2998909943": "https://digitalcommons.fairfield.edu/cgi/viewcontent.cgi?article=1241&context=nursing-facultypubs",
}
out = {}
jfc = requests.get("https://elischolar.library.yale.edu/journal-of-financial-crises/vol1/iss1/1/", headers=UA, timeout=40).text
m = re.search(r'citation_pdf_url"?\s+content="([^"]+)"', jfc) or re.search(r'content="([^"]+)"\s+name="citation_pdf_url"', jfc)
out["jfc_page_mentions"] = {"citation_pdf_url": m.group(1) if m else None,
                            "license_cc": "creativecommons.org" in jfc, "open access phrase": "open access" in jfc.lower()}
if m:
    URLS["W2954967843"] = m.group(1)
for k, u in URLS.items():
    r = requests.get(u, headers=UA, timeout=60, allow_redirects=True)
    out[k] = {"status": r.status_code, "content_type": r.headers.get("content-type"), "bytes": len(r.content),
              "starts_pdf": r.content[:4] == b"%PDF", "final_url": r.url}
    time.sleep(0.5)
json.dump(out, open("verification/crosscheck_live_pdfs_out.json", "w"), indent=1)
print(json.dumps(out, indent=1))
