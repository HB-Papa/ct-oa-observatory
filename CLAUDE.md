# Connecticut Open Access Observatory — rules for every session

Read PROGRESS.md and DECISIONS.md at the start of every session. Update PROGRESS.md (done, next, open questions) at the end of every session. Record every real choice in DECISIONS.md (the choice, the alternatives, why).

## Who this is for
Chris has an MLIS (USC, 2025) and is moving into academic librarianship. Comfortable with data (R, Power BI, Tableau, SPSS, MARC21, Dublin Core), not a professional software engineer. Explain technical choices in plain language so they can be defended in a job interview. This project stands on its own. **Do not describe it on the site as a companion or sibling to Open Sun, and do not link to Open Sun from the site** (Chris, 2026-11-16). It has its own visual design: Chris rejected reusing Open Sun's look on 2026-11-16. The design is the "research report" direction (see DECISIONS.md): white page, Source Serif 4 headlines, Public Sans text, a single reading column with numbered figures, dark red accent. Chart colors are validated with the dataviz palette validator; re-run it before changing any chart color.

## What the project answers
1. Share of each institution's research that is free to read, by OA status (diamond, gold, hybrid, bronze, green, closed).
2. Change from 2015 to 2025 (last complete year). 2026 shown separately and labeled incomplete (indexing lag).
3. Which fields (OpenAlex topics) and publishers account for the most output and the most closed articles.
4. Estimated APC spending. Every figure labeled as an estimate.
5. Green OA opportunity: closed or bronze articles that publisher policy would likely allow in a repository.

## Phases — stop and wait for Chris's approval at each ★
0 Setup, env check, CLAUDE.md, API notes, key list, cost estimate ★
1 Institution list with IDs and counts ★
2 OpenAlex harvest + data quality report ★
3 Metrics + verification agent report ★
4 First version locally: Overview + Yale or UConn profile ★
5 Deployment (ask before creating a public GitHub repo or deploying) ★
6 Cross-checks and enrichment + deposit policies ★
7 Full site, Compare, downloads, Methods, accessibility audit ★
8 Monthly refresh action ★
9 Write-ups ★
Build a small working version first (Overview + one profile, deployed) before expanding.

## Data sources and roles
- **OpenAlex is the only source of truth for numbers on the site.** API key required (2026). Key in `.env` as `OPENALEX_API_KEY`, never hardcoded, never committed.
- Prefer `group_by` for counts. Use `select=` and `per_page=100`. Harvest full work records only where the analysis needs them.
- **Before any large pull, write a cost estimate. If it exceeds one day's free allowance, STOP and ask.**
- Validation/enrichment sources (Unpaywall, OpenAIRE, CORE, DOAJ, OpenAPC, Open Policy Finder) each have their own labeled role. **Never blend their numbers into OpenAlex-based figures.** Unpaywall is not independent of OpenAlex (same maker, OurResearch); say so.
- If a validation source is unavailable or too costly, skip it, note why in DECISIONS.md, keep going.
- Open Policy Finder fallback (no key): proxy = closed article in a journal where other articles have an accepted-manuscript repository copy. Label as a proxy everywhere.
- Out of scope: BASE, Semantic Scholar, Crossref, preprint servers. List ideas in a "Future sources" note only.
- Never create accounts or request keys on Chris's behalf. Ask before registering for any token or setting up GitHub secrets.

## Counting rules
- A work counts for an institution if any author lists that affiliation (lineage filter).
- Statewide totals deduplicate by work ID. Show statewide totals with and without Yale.
- Exclude retracted works and paratext. Work types: articles and reviews at minimum (final list agreed with Chris, recorded in DECISIONS.md).
- Years: 2015–2025 complete; 2026 separate and labeled incomplete.

## APC methodology
- Upper bound: list price across all authorships.
- More defensible: corresponding-author attribution via `corresponding_institution_ids`; report how many works have it filled.
- Show share from OpenAPC (actual payments) vs list prices. Note full fee credited to each institution when several corresponding authors exist. Note list prices rise, so older years may be overstated.

## Technical rules
- Python 3 pipeline. Raw API responses cached in `data/raw/<source>/` and never re-downloaded. Tidy Parquet tables, queried with DuckDB.
- One script per step, each rerunnable alone, plus one command that runs everything.
- Each run writes a snapshot date and a query log.
- pytest tests for metric functions with small known-answer fixtures.
- Static site (Astro), deployed on Vercel.
- Pages: Overview, one profile per institution, Compare (2–4), Methods and Limitations, Data Downloads (CSVs + data dictionary), About, Changelog. (The original brief had About link to Open Sun; Chris removed that on 2026-11-16.)
- Monthly GitHub Action reruns the OpenAlex pipeline and rebuilds. Cross-checks quarterly or by hand.
- **Git: never commit `data/raw/`, `.env`, or any file over 50 MB. Publish only derived tables.**
- Commit email: `341102662+HB-Papa@users.noreply.github.com`.

## Non-negotiables
- **Accuracy:** every number on the site traces to a script and a saved query. Make nothing up. No unlabeled estimates. Spot-check counts against the OpenAlex web UI and save results in `docs/verification.md`.
- **Limitations to state honestly:** affiliation errors, how OA status is classified (journal-dependent), list price vs paid, indexing lag, humanities and book coverage gaps, source disagreements from cross-checks.
- **Privacy and tone:** institution totals only. No pages about individual researchers. No shaming. The article-level repository candidate list is a CSV download for librarians, never shown on the site.
- **Accessibility (WCAG 2.2 AA):** every chart has a written summary and a data table. Never color alone; colorblind-safe palettes; OA status colors only where they pass contrast, paired with labels or patterns. Full keyboard use. Reflow at 400% zoom.
- **No tracking:** no analytics, cookies, accounts, external fonts, or scripts that phone home. Self-host fonts.
- **Licenses:** OpenAlex is CC0; publish derived data as CC0 unless a source's terms forbid it. Check Open Policy Finder, CORE, OpenAIRE, DOAJ, OpenAPC terms before publishing anything derived from them; add required attributions; flag conflicts to Chris.

## Subagents
- Docs agent: checks API details before coding (`docs/api-notes.md`).
- Verification agent: recomputes key figures from raw data without seeing analysis code; reports mismatches.
- Cross-check agent: runs sample comparisons against Unpaywall, OpenAIRE, CORE, DOAJ.
- Accessibility agent before launch: axe, Lighthouse, manual keyboard pass.

## Phase 9 writing voice (abstract, resume bullets, interview notes)
Concise and plain. No em dashes, no colons or semicolons, no unnecessary adjectives. Every claim based on real data and on what was actually built. No embellishment.
