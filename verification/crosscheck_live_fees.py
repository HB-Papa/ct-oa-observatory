"""Cross-check agent, part 7b: read the fee wording on the Econometric Society pages DOAJ cites
for Quantitative Economics and Theoretical Economics (2 requests). Prints sentences mentioning fees.
Run: python -m verification.crosscheck_live_fees"""
import re, time, requests
UA = {"User-Agent": "Mozilla/5.0 (compatible; oa-crosscheck/1.0)"}
for name, u in {"QE": "https://www.econometricsociety.org/publications/quantitative-economics/submissions/instructions-for-submitting-articles",
                "TE": "https://www.econometricsociety.org/publications/theoretical-economics/submission-guidelines"}.items():
    r = requests.get(u, headers=UA, timeout=40)
    text = " ".join(re.sub(r"<[^>]+>", " ", re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", r.text)).split())
    print(name, r.status_code, len(text))
    for s in re.split(r"(?<=[.!?])\s+", text):
        if re.search(r"fee|charge|\$\s?\d|waive", s, re.I):
            print("  -", s[:300])
    time.sleep(0.5)
