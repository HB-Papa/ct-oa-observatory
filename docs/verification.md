# Verification log

Spot checks comparing pipeline counts with the OpenAlex web interface (openalex.org). Each check opens the web interface with the same filter the pipeline uses and reads the result count.

## Phase 2 harvest, snapshot 2026-11-15 (checked 2026-11-15 in the browser)

Common filter: `type:article|review,is_retracted:false`, plus what is listed. "Harvested" is computed from `data/derived/works.parquet` and `work_institutions.parquet`.

| # | Check | Extra filter | Harvested | Web interface | Result |
|---|---|---|---:|---:|---|
| 1 | Wesleyan, 2020 | `authorships.institutions.lineage:I100538780,publication_year:2020` | 280 | 280 | Match |
| 2 | Yale, 2025 | `authorships.institutions.lineage:I32971472,publication_year:2025` | 13,248 | "about 13,250" | Match (the web interface rounds large counts; the API `group_by` count is 13,248) |
| 3 | UConn + UConn Health, 2023 | `authorships.institutions.lineage:I140172145\|I75929689,publication_year:2023` | 4,285 | 4,285 | Match |
| 4 | Connecticut College, 2026 | `authorships.institutions.lineage:I4498119,publication_year:2026` | 291 | 291 | Match (includes 251 repository records, see data-quality.md §4) |
| 5 | Coast Guard Academy, 2015–2025 | `authorships.institutions.lineage:I186274478,publication_year:2015-2025` | 200 | 200 | Match |
| 6 | Quinnipiac, 2024, gold | `authorships.institutions.lineage:I43267033,publication_year:2024,open_access.oa_status:gold` | 62 | 62 | Match |
| 7 | Statewide, 2025, closed | all 18 IDs, `publication_year:2025,open_access.oa_status:closed` | 5,722 | 5,722 | Match |
| 8 | Statewide, 2019, diamond | all 18 IDs, `publication_year:2019,open_access.oa_status:diamond` | 820 | 820 | Match |

**Result: 8 of 8 match.**

## Internal check: harvest vs API `group_by` counts
`docs/data-quality.md` §1 compares every institution-year (17 institutions × 12 years = 204 cells) with the phase 1 `group_by` counts. After the author-cap fix below, all 204 match exactly.

## Problem found and fixed: author lists capped at 100
- **Found:** the first build left 1,588 works with no Connecticut institution, and Yale was 1,408 works short of its `group_by` count. Every one of those works had exactly 100 authorships.
- **Cause:** OpenAlex list results include at most 100 authorships per work. Large collaborations (median 424 authors among affected works) can list a Connecticut author after position 100.
- **Fix:** `pipeline/s03b_fetch_full_authorships.py` fetches each of the 3,320 capped works individually, which returns the full author list and costs 0 credits. `s04` uses the full record for those works.
- **After:** 0 works without an institution; 204 of 204 institution-years match.
- **Remaining edge:** 7 works have exactly 5,000 authorships in the single-record response, which may be a second cap. All 7 already match a Connecticut institution, so totals are unaffected; a second Connecticut institution past author 5,000 could be missed on those 7 works.

## Pre-launch QA check against live OpenAlex (2026-11-19)

Published data: OpenAlex as of 2026-11-17 (monthly refresh run 44108525935).

- **Statewide total, 2015-2025.** Live OpenAlex count today: 176,808. Published articles plus excluded records from the 2026-11-17 download: 174,990 + 2,611 = 177,601. Difference -793 (0.45%).
- **Cause: OpenAlex changed, not the pipeline.** The 2026-11-17 run saved OpenAlex's own per-institution counts, and the download matched them exactly (`data/derived/quality/completeness_by_institution_year.csv`, gap 0.00%). Two days later the same queries give different counts: Yale 2015 8,530 then 8,434; Yale 2022 11,642 then 11,515; UConn 2015 3,685 then 3,615; UConn 2025 4,640 then 4,654. Older years fell and recent years rose, consistent with OpenAlex merging and reclassifying records while new ones are indexed.
- **USCGA open access breakdown, live versus published** (OpenAlex diamond = our diamond plus fee not confirmed): diamond 35 and 35, gold 23 and 23, hybrid 12 and 12, bronze 22 and 22, green 29 and 25, closed 75 and 77. Small moves of the same kind.
- **Action:** the Methods page now states that OpenAlex changes daily and that figures reflect the download date. The monthly refresh's -2% to +5% statewide gate allows for changes of this size.

## Fairfield University accuracy review (2026-11-24)

Published figures: OpenAlex as of 2026-11-17. Fairfield 2015-2025: 1,752 articles, 947 free to read (54.1%).

- **Download complete.** All 11 years matched OpenAlex's own counts on 2026-11-17 (1,790 records). 38 were excluded by the project's scope rules (22 meeting abstracts, 17 repository records without a DOI, minus overlap), leaving 1,752.
- **Affiliations, strict check** (`verification/fairfield_affiliations.py`). The earlier check accepted any affiliation containing "Fairfield", which also matches other places named Fairfield. The strict check needs Fairfield University, one of its schools, or Fairfield with Connecticut, CT or the 06824/06825 ZIP codes. Result: 1,777 of 1,790 (99.3%) confirmed. Of the other 13, six are Fairfield University in another form ("Fairfield U", two "Fairefield University", "Farfield University", "Université Fairfield (États-Unis)", "Fairfield College" listed with Holy Cross), one has no affiliation text (a RePEc paper), and **six are not Fairfield University**: five from the Fairfield Institute of Management and Technology (Delhi, India) and one from a program in Fairfield, New Jersey. All six were counted (3 closed, 2 hybrid, 1 green). Removing them changes Fairfield's share from 54.05% to 54.07%. A correction rule for them was added to `pipeline/s04_build_tables.py` and, written separately, to `verification/recompute.py`; both flag the same six works. It takes effect at the next refresh.
- **Hand check of 12 random articles** against live OpenAlex records: 12 of 12 confirmed as Fairfield by affiliation text, and 12 of 12 with the same open access status.
- **Diamond share explained.** Fairfield's diamond share (7.6%, statewide 0.9%) comes from high-energy physics: 132 of its 134 diamond articles are in Journal of High Energy Physics, Physics Letters B and European Physical Journal C, which are free to authors through the SCOAP3 library consortium. 293 Fairfield articles (17%) have 100 or more authors, consistent with membership of a large physics collaboration. Most are from 2015 to 2017 (63 in 2017), which explains that year's spike (215 articles, 66% free to read).
- **Digital Commons.** 108 closed Fairfield articles had a DigitalCommons@Fairfield record marked not free on 2026-11-15. Between 2026-11-17 and 2026-11-24, OpenAlex began treating 30 of them as free (green), plus 11 other Fairfield articles via other repositories (`verification/fairfield_newly_green.csv`). Six of the remaining 78 repository pages were checked: none offers a public full text (each links to the publisher or to Fairfield's library login), so OpenAlex is right to call them closed. The repository gap for Fairfield noted in the 2026-11-15 cross-check is now largely closed at the source and will show at the next refresh.
- **Live OpenAlex today vs published:** green 225 vs 186, closed 776 vs 805, others within 8. The difference is the repository change above plus ordinary daily change.
