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
