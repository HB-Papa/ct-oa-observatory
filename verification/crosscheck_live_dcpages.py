"""Cross-check agent, part 5c: read Digital Commons landing pages for download/embargo cues.
Run: python -m verification.crosscheck_live_dcpages  (4 requests; prints short snippets only)"""
import re, time, requests
UA = {"User-Agent": "Mozilla/5.0 (compatible; oa-crosscheck/1.0)"}
for wid, u in {"W2183917196": "https://digitalcommons.fairfield.edu/chemistry-facultypubs/42/",
               "W2442085864": "https://digitalcommons.newhaven.edu/economics-facpubs/9/",
               "W2998909943": "https://digitalcommons.fairfield.edu/nursing-facultypubs/235/",
               "W2954967843": "https://elischolar.library.yale.edu/journal-of-financial-crises/vol1/iss1/1/"}.items():
    h = requests.get(u, headers=UA, timeout=40).text
    text = re.sub(r"<[^>]+>", " ", h); text = " ".join(text.split())
    cues = {k: bool(re.search(k, text, re.I)) for k in ["Download", "embargo", "Restricted", "campus", "not available", "Comments", "author's accepted", "preprint", "Creative Commons", "open access"]}
    dl = re.findall(r'id="(?:beta_7-3|alpha-pdf)"[^>]*>|class="btn"[^>]*href="([^"]+)"', h)
    print(wid, cues)
    i = text.find("Comments")
    if i >= 0: print("   comments:", text[i:i+200].split("Repository Citation")[0])  # stop before author names
    for kw in ("Download", "embargo"):
        j = text.lower().find(kw.lower())
        if j >= 0: print(f"   {kw}:", text[max(0,j-80):j+120])
    time.sleep(0.5)
