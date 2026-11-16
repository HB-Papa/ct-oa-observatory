# Phase 3 verification: independent recomputation

**Result: PASS on all figures** (after one fix, described below). Snapshot 2026-11-15, checked 2026-11-16.

## How it was done
An independent verification agent recomputed the key figures **from the raw OpenAlex cache** with its own code. It was not allowed to read the pipeline code (`pipeline/`), the tests, or the derived Parquet tables. It was given only the raw data location and plain-language definitions. Only after computing did it compare its numbers with the published CSVs in `data/derived/metrics/`.

Its scripts are in `verification/` and can be rerun.
- `recompute.py` builds `mine.json` from the raw cache.
- `compare.py` compares it with the published CSVs and writes `comparison.json`.
- `sanity.py` runs extra checks and writes `sanity_out.txt`.

Pass rules: exact match for counts, within $1 for dollar sums, within 0.001 for shares.

**Handling the 100-author cap.** List pages cut author lists at 100. The agent replaced all 3,320 works with 100 or more authors by their full single-work records, and every one had a full record available. It found no work that appeared twice across list pages.

## Results

| # | Figure | Cells compared | Result |
|---|---|---:|---|
| 1 | Statewide in-scope works per year, 2015–2026 | 12 | PASS |
| 2 | Works per institution, 2015–2025 (17 institutions + 2 statewide sets) | 19 | PASS |
| 3 | OA status counts, statewide and statewide without Yale, 2015–2025 | 12 | PASS |
| 4 | Free-to-read counts and shares | 19 + 19 | PASS |
| 5 | APC estimates: works, works with a list price, USD. Statewide, without Yale, Yale, UConn, Quinnipiac, Bridgeport; both methods | 12 × 3 | PASS after fix |
| 6 | Corresponding-institution coverage | 19 + 19 | PASS |
| 7 | Statewide top 5 publishers by closed works | 15 | PASS |

Selected values (independent = published):
- Works per year, 2015 to 2026: 13,066, 13,536, 13,884, 14,182, 14,992, 17,338, 17,488, 17,112, 17,052, 18,180, 19,382 and 17,522. Rule A excluded 1,827 works, 409 of them in 2026.
- Statewide works 2015–2025: 176,212. Without Yale: 62,594.
- Free-to-read share 2015–2025: statewide 0.6681. Without Yale: 0.5920.
- Corresponding coverage 2015–2025: 144,363 of 176,212 works (0.8193).
- Top publishers by closed works: Elsevier (15,940 closed of 42,383), Springer Nature (6,241 of 21,949), Wiley (6,082 of 16,454), Wolters Kluwer (5,773 of 10,092), Informa (4,475 of 7,167).

## Mismatch found and fixed
- **What:** On the first comparison, 1 of 12 APC rows failed: the corresponding-author estimate for "statewide without Yale". The independent figure was $16,738,679 across 7,230 works. The published figure was $17,758,370 across 7,559 works.
- **Cause:** The pipeline credited a "without Yale" work whenever *any* Connecticut institution was corresponding, including Yale. That put 329 works (about $1.02M) into the figure where Yale was the only corresponding Connecticut institution. This was a definition error in the pipeline, not in the verification.
- **Fix:** For the "without Yale" figure, only a non-Yale institution counts as corresponding. The new function is `metrics.any_corresponding(wi, exclude=("yale",))`, with a known-answer test `test_apc_statewide_without_yale_ignores_yale_corresponding`.
- **After:** The published figure is $16,738,679 across 7,230 works, an exact match. Rerunning `verification/compare.py` gives PASS on every figure.

## Sanity observations (for follow-up, not failures)
- **The 100-author fix matters.** Without it, Yale would lose 1,408 works and Fairfield 162 (about 9% of Fairfield's output). The published counts match the full author lists.
- **The University of Bridgeport has the highest free-to-read share, 0.781**, with 22% diamond. Most of it comes from IEEE Access, MDPI and diamond engineering journals.
  - 30% of Bridgeport's works have publisher "Unknown", including 36 classed hybrid.
  - Its output roughly doubles in 2025, to 120 works.
  - Worth checking its affiliation and source metadata before the profile is published. This was done in the double-check below.

---

# Double-check (2026-11-16, requested by Chris before approving phase 3)

Four extra checks, with Bridgeport as the main focus. One real affiliation error was found and corrected (Trinity), and one classification issue was found and is waiting on a decision ("diamond"). After the correction, every figure passes again on both independent routes.

## Check A: Are the affiliations real? (all 17 institutions)
Script: `verification/affiliation_check.py`. For every work credited to an institution, it reads the **raw affiliation text** of the authors OpenAlex matched to that institution and asks whether any of it names the institution. Results are in `verification/affiliation_check.csv`, with unconfirmed cases in `affiliation_unconfirmed_samples.csv`.

| Institution | Works 2015–2025 | Text names the institution |
|---|---:|---:|
| **University of Bridgeport** | 754 | **100.0%** |
| University of Hartford | 1,205 | 100.0% |
| Yale, UConn | 116,949 / 45,618 | 99.9% |
| 12 others | | 99.3% to 99.8% |
| Trinity College | 862 | 98.4% |
| Central Connecticut State | 1,394 | 97.2% |

- **Bridgeport's affiliations are genuine.** Every one of its works has an author whose own affiliation text says "University of Bridgeport".
- **Most "unconfirmed" cases are typos or abbreviations**, which are real affiliations. Examples: "Central. Connecticut State University", "Cent. Conn. State Univ.", "Weslyan", "Qunnipiac", "Scared Heart", "University of Conneticut", "South. Conn. State Univ.".
- **Trinity has a systematic error, now corrected.** 14 works in 2015–2025 (plus 2 in 2026) are by authors at **Washington College in Chestertown, Maryland**, which OpenAlex also links to Trinity College. Trinity was founded as "Washington College" in 1823. The OpenAlex page for W4392406531 shows the author linked to both institutions.
  - **Fix:** `AFFILIATION_CORRECTIONS` in `pipeline/s04_build_tables.py`. A Trinity credit is removed when the matched authors' affiliation text names Washington College and never names Trinity. The rule has 2 known-answer tests.
  - Trinity goes from 862 to 848 works, and statewide from 176,212 to 176,198.
- **Yale has a small amount of noise, not corrected.** About 30 of roughly 129,000 works (0.03%) have a wrong match. Sources include an NYC school called "The Collegiate School" (Yale's founding name), a Northwestern University center, and Quinnipiac's Netter School of Medicine. Too small to change any figure, so it's recorded as a limitation.

## Check B: The same counts by a different route (live OpenAlex API)
Script: `verification/api_oa_crosscheck.py`, about 30 credits. For statewide, Bridgeport, Trinity, Sacred Heart and Yale, it asks OpenAlex for counts by OA status (2015–2025), then subtracts the rule A records and the Trinity corrections.
- **58 of 60 cells match exactly.**
- The 2 statewide cells that differ (hybrid −1, closed +1) are one article, W7160837712. OpenAlex's count index lists it as hybrid, but its own record says closed, which is what we harvested. This is an inconsistency inside OpenAlex, not in our data.

## Check C: Every finding reported to Chris, recomputed after the correction

| Finding | Recomputed |
|---|---|
| 66.8% of 2015–2025 research free to read, 59.2% without Yale | 66.81% and 59.20%. Holds |
| Rose from 58.6% (2015) to 74.0% (2023), dipped to 70.6% (2025) | Holds |
| Shares range from Sacred Heart 44% to Bridgeport 78% | 44.2% to 78.1%. Holds |
| Elsevier has the most closed articles, 15,940 of 42,383 (38%) | Now 15,939 of 42,381 (37.6%) after the correction. Holds |
| Highest closed shares among large publishers: Informa 62%, Wolters Kluwer 57% | Holds for publishers with at least 3,000 works. Next are the American Chemical Society (54%) and SAGE (52%) |
| APC estimate $60.2M (corresponding) and $145.4M (upper bound) | $60,235,164 and $145,372,638. Holds |
| **The 2023–2025 dip "likely reflects the delay before authors post free copies in archives (green)"** | **Wrong as stated.** Green is flat (12.7%, 13.1%, 12.9%). What falls is **bronze** (15.9%, 12.7%, 8.1%) while closed rises. Bronze includes publishers that open articles a year or more after publication, so the dip is consistent with bronze arriving late. The explanation is corrected here and will be retested with the next snapshot. |
| Bridgeport output doubles in 2025, and 30% of its works have no known publisher | 60 (2024) to 120 (2025), and 30.2% (228 works). Holds |

## Check D: OpenAlex web interface
| Check | Pipeline (before rule A) | Web interface | Result |
|---|---:|---:|---|
| Bridgeport, 2015–2025, diamond | 169 | 169 | Match |
| Sacred Heart, 2015–2025, closed | 756 (751 after rule A removes 5) | 756 | Match |
| Trinity work W4392406531 | linked to Trinity | shows both "Washington College" and "Trinity College" | Confirms the error |

## Independent recomputation, rerun
The verification agent's script (`verification/recompute.py`) now applies the same Trinity correction, written separately from the pipeline from the plain-language rule. **Result: PASS on all 12 figure groups, exact.**

While rerunning it, a problem in the *verification* script surfaced. It read every cached page that looked like a harvest page, so it picked up the ID-only pages from Check B (1,308 records with no fields). It now reads only pages whose `select` includes authorships, giving 195,561 records with 0 duplicates. The pipeline was never affected, because it looks up cached responses by their exact query.

## Issue found, decision needed: what "diamond" means in OpenAlex
The Bridgeport review showed that **OpenAlex labels an article "diamond" when the journal is open access and OpenAlex has no fee recorded for it, not only when the fee is known to be $0.** Three of Bridgeport's top "diamond" journals have `apc_usd: null`, no price data, and are not in DOAJ. One of them is Scientific Research Publishing's *Open Journal of Business and Management*.

Statewide, 2015–2025 diamond works (9,958):

| Basis | Works | Share |
|---|---:|---:|
| In DOAJ, fee recorded as $0 | 1,540 | 15.5% |
| Not in DOAJ, fee recorded as $0 | 69 | 0.7% |
| In DOAJ, no fee recorded | 3,760 | 37.8% |
| Not in DOAJ, no fee recorded | 4,589 | 46.1% |

The largest unverified journals are Cureus (549 works), Oncotarget (149), Journal of Athletic Training (110) and Archives of Pathology & Laboratory Medicine (85). Oncotarget has charged authors fees.

**Effect:**
- Free-to-read shares are unaffected, because these articles are free to read either way.
- The diamond share (5.7% statewide) is likely overstated and gold understated.
- APC estimates are likely somewhat understated, because diamond works are not counted.

**Resolved 2026-11-16 (Chris chose to split now).** The site reports `oa_category`:
- **diamond**: fee confirmed $0, 1,609 works (0.9%) statewide in 2015–2025.
- **oa_fee_unconfirmed**: 8,349 works (4.7%).

The independent recomputation implements the same split and passes on all 35 category cells (statewide, without Yale, Bridgeport, Yale, Trinity), with every other figure group still exact. Bridgeport has 3 confirmed diamond works and 166 with the fee not confirmed.
