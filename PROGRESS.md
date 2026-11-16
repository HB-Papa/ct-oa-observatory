# Progress

## Current phase
Phase 5: deployment (live at https://ct-oa-observatory.vercel.app, awaiting Chris's approval)

## Done
- 2026-11-15: Created project folder `Desktop/Access/ct-oa-observatory`, CLAUDE.md, PROGRESS.md, DECISIONS.md.
- 2026-11-15: Environment check (see below).
- 2026-11-15: Docs agent wrote `docs/api-notes.md` (all 7 sources, keys table, license flags, future sources).
- 2026-11-15: Phase 0 approved (Astro chosen, UConn Health rolled up, work types agreed).
- 2026-11-15: Python venv + pipeline client with cache and query log. Phase 1 table in `docs/phase1-institutions.md` (69 credits).
- 2026-11-15: Phase 1 approved: 17 institutions (15 named + Bridgeport + Saint Joseph), universities only.
- 2026-11-15: Phase 2 harvest: 195,561 works, 1,962 credits ($0.20); full records for 3,320 large-collaboration works (0 credits). All 204 institution-years match group_by counts. 8/8 web spot checks match (docs/verification.md). Data quality report in docs/data-quality.md. 6 pytest tests pass.
- 2026-11-15: Draft cost estimate in `docs/cost-estimate.md` (~3,100–4,100 credits, under one free day).
- 2026-11-16: Phase 2 approved with rule A (exclude repository records without DOI, 1,827 works; 193,734 remain).
- 2026-11-16: Outreach pitch in `docs/pitch.md`, rewritten for readers new to open access.
- 2026-11-16: Independent verification agent recomputed 7 figure groups from raw data: all PASS after fixing the no-Yale corresponding APC rule (docs/verification-phase3.md). 20 pytest tests pass.
- 2026-11-16: Phase 3 metrics: `pipeline/metrics.py` (definitions), `pipeline/s06_metrics.py` (11 CSVs in data/derived/metrics/ + manifest.json). 19 pytest tests pass. `python -m pipeline.run_all` reruns everything from cache in ~2 min with 0 API calls and identical output.
- 2026-11-16: Double-check (second half of docs/verification-phase3.md). Bridgeport affiliations 100% confirmed. Trinity / Washington College error corrected (14 works). Live API route matches 58 of 60 cells (the 2 others are one OpenAlex index inconsistency). Independent recompute PASS on all 12 groups after the correction. Trend explanation corrected (bronze, not green). 22 pytest tests pass.
- 2026-11-16: Diamond split approved and applied: `oa_category` with diamond (fee confirmed $0) and oa_fee_unconfirmed. Metric files renamed `oa_category_*.csv`. Independent recompute PASS on all groups (35 of 35 category cells). Full pipeline rerun reproduces identical output. 24 pytest tests pass.
- 2026-11-16: Phase 3 approved. Phase 4 first build: Astro 7.4.7 site in `site/` (Overview + UConn profile), zero scripts, self-hosted fonts, Astro telemetry disabled, no external requests. Chart palette validated with the dataviz validator. axe: 0 violations on Overview. Reflows at 320px with no page overflow.
- 2026-11-16: Chris disliked the Open Sun look. Three mockups compared; Chris chose "research report". Site restyled (Source Serif 4 + Public Sans, white, numbered figures, key findings). Mockups and old fonts removed. Chart palette re-validated on the new surfaces; green, bronze and closed adjusted for 4.5:1 in-bar labels. axe: 0 violations on both pages in light and dark (remaining 'needs review' items are SVG axis labels at 7.6:1, checked by hand). Keyboard pass OK (skip link, focus order, table toggles). Reflows at 320px on both pages. Text scanned for run-together words.
- 2026-11-16: Phase 4 approved (Open Sun mention removed from the site).
- 2026-11-16: Phase 5: public repo https://github.com/HB-Papa/ct-oa-observatory pushed (MIT code, CC0 data; parquet, researcher-email samples and pitch kept local). site/vercel.json with no-script CSP and noindex header.
- 2026-11-16: Deployed: https://ct-oa-observatory.vercel.app (CLI deploy; headers, no cookies, no scripts, no external requests checked live).

## Environment (2026-11-15)
| Tool | Status |
|---|---|
| Python 3 | 3.15.2 installed by Chris |
| Node | v24.20.0 OK |
| npm | 11.19.0 OK |
| git | 2.55.0 OK |
| GitHub CLI | 2.102.0 OK, logged in as HB-Papa |
| Vercel CLI | 63.1.2, logged in (team hb-papa) |
| make | Missing (not needed; a Python `run_all` script replaces the Makefile on Windows) |

## Next
- Optional: Chris grants Vercel's GitHub app access to HB-Papa/ct-oa-observatory so pushes deploy automatically; otherwise redeploy with `vercel deploy --prod`.
- Phase 6: cross-checks (Unpaywall, OpenAIRE, CORE, DOAJ, OpenAPC) and deposit policies / green proxy.

## Open questions
- UConn Health is not in UConn's OpenAlex lineage; roll-up uses an OR filter (UConn | UConn Health), deduplicated.
- Phase 6: use DOAJ data to move works out of "oa_fee_unconfirmed" (8,349 statewide, 2015–2025) into diamond or gold where DOAJ confirms the fee.
- Green OA opportunity moved to phase 6 (needs journal-level queries).
- CORE: Chris's reading is the individual free licence; revisit before phase 6.
