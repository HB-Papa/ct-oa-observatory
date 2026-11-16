# OpenAlex cost estimate (phase 0 draft)

Prices from `docs/api-notes.md` (checked 2026-11-15). 1 credit = $0.0001. Free key = 10,000 credits ($1.00) per day, reset at midnight UTC. A new account gets its first $1 released at $0.10 per 5 minutes.

| Call type | Credits |
|---|---|
| Single work by ID or DOI | 0 |
| Filtered list page (up to 100 results) | 1 |
| `group_by` on a filtered list | 1 |
| Search | 10 (we will avoid search) |

## How the estimate is built
1. **Counts come from `group_by`, not downloads.** One call returns the count for every OA status (or year, or topic) for one filter. Example: 16 institutions × 12 years × 1 call grouped by `oa_status` = 192 credits.
2. **Full records only where needed.** APC, corresponding author, and journal-level green proxy need per-work fields, so those works are downloaded once with `select=` and `per_page=100`. Cost = number of works ÷ 100.
3. **Statewide pull is deduplicated at the source.** One filter combining all institution IDs (`authorships.institutions.lineage:A|B|C`) returns each work once, so collaborations aren't paid for twice.
4. **Validation lookups by DOI are free** (single-record calls cost 0).

## Rough sizes (to be replaced by real counts in phase 1)
These are placeholders, not data. Phase 1 gets the real numbers for about 30 credits.

| Step | Assumed volume | Credits |
|---|---|---|
| Phase 1: find CT institutions (`geo.region:Connecticut`, 488 rows) + per-institution counts | ~5 pages + ~20 group_by | ~30 |
| Phase 2 counts: OA status × year × institution, topics, publishers | ~600 group_by calls | ~600 |
| Phase 2 records: all CT works 2015–2026, articles + reviews | ~250,000–350,000 works | ~2,500–3,500 |
| Validation sample (500 DOIs) | single lookups | 0 |
| **Total** | | **~3,100–4,100 credits (about $0.31–$0.41)** |

That fits inside one day's free allowance with room for reruns. The monthly refresh would cost about the same.

## Unknowns to test before the big pull
- The docs don't say whether cursor paging or `select=` changes the per-page cost. Before phase 2, run 3 cursor pages and read the usage figure the API reports, then update this file.
- If the real work count from phase 1 pushes the total past 10,000 credits, stop and ask Chris.

## Update after phase 1 (2026-11-15)
Real counts replace the placeholders. Statewide, deduplicated, articles and reviews: 177,841 for 2015–2025 plus 17,955 for 2026, about 196,000 works. At 100 per page that is about **1,960 credits** for the full-record harvest, plus about 600 for the `group_by` counts, about **2,600 credits ($0.26)** in total. That fits inside one free day (10,000 credits). Phase 1 itself used 69 credits. The cost header `X-RateLimit-Credits-Used` is now logged on every call, so actual spend is recorded, not estimated.

## Phase 6 (2026-11-16)
Estimate before running: about 100 credits for the green proxy (10,045 journals, 100 per `group_by` request) and about 100 for journal ISSN and price lookups. Actual, from the query log: **207 credits ($0.02)**. Green proxy 101, OpenAPC price lookups 68, DOAJ ISSN lookups 34, filter tests 4. Unpaywall (510 lookups), OpenAIRE (11 requests), DOAJ (84 requests) and the OpenAPC file download are free and do not use OpenAlex credits.
