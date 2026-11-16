# Decisions

Each entry: the choice, the alternatives, and why. Newest at the bottom.

## 2026-11-15 — Project lives in its own folder
- **Choice:** `Desktop/Access/ct-oa-observatory`, separate repo from Open Sun.
- **Alternatives:** a section inside Open Sun.
- **Why:** Matches how Open Sun and Open Brief are kept separate. Different stack (Python pipeline + Astro) and a different audience.

## 2026-11-15 — Astro for the site (approved by Chris)
- **Choice:** Astro static site, deployed on Vercel.
- **Alternatives:** Next.js (Open Sun's stack), Quarto, Observable Framework.
- **Why:** The site is read-only pages built from data files. Astro ships plain HTML with no JavaScript unless a page asks for it, which makes accessibility and the no-tracking rule easier to prove. Next.js would work but brings a React runtime we don't need. Quarto is attractive for an R user but harder to give a custom, accessible multi-page design. Observable Framework is strong for charts but adds a data-loader model on top of the Python pipeline. Open Sun's design tokens (CSS custom properties) carry over unchanged, so the sites still look related.

## 2026-11-15 — One Python command instead of a Makefile (proposed)
- **Choice:** `python -m pipeline.run_all` runs every step in order; each step is also runnable alone.
- **Alternatives:** Makefile.
- **Why:** `make` isn't installed on this Windows machine and isn't standard on Windows. A Python runner works the same on Windows, Mac, and the GitHub Action.

## 2026-11-15 — Self-hosted fonts
- **Choice:** Install fonts as npm packages (Fontsource) so they are served from our own domain.
- **Alternatives:** Google Fonts link.
- **Why:** The no-tracking rule forbids external fonts that phone home. (Open Sun gets the same result through Next.js's build-time font download.)

## 2026-11-15 — UConn Health rolled up into UConn
- **Choice:** UConn Health counts under UConn through OpenAlex's institution lineage. No separate UConn Health row.
- **Alternatives:** UConn Health as its own institution; rolled up plus a separate row.
- **Why:** Chris's call. UConn Health is part of the university, and lineage already joins them. Phase 1 will confirm UConn Health's OpenAlex ID sits under UConn's lineage.

## 2026-11-15 — Work types
- **Choice:** Articles and reviews for every metric. Books and book chapters reported as a separate count only.
- **Alternatives:** articles and reviews only; all scholarly types.
- **Why:** Articles and reviews are where OA status and APCs are well defined. Showing book counts on their own keeps the humanities coverage gap visible without mixing book OA (which works differently) into article rates. Retracted works and `type:paratext` are excluded.

## 2026-11-15 — Open Policy Finder is not the published method
- **Choice:** The green OA opportunity on the site uses the OpenAlex-only proxy (closed article in a journal where other articles have an accepted-manuscript repository copy), labeled as a proxy. Open Policy Finder, if Chris gets a key, is used only for an aggregate check reported on the Methods page.
- **Alternatives:** Build the candidate list from Open Policy Finder policies.
- **Why:** Open Policy Finder data is CC BY-NC-ND 4.0, which conflicts with releasing derived data as CC0.

## 2026-11-15 — CORE used under the individual free licence (Chris's reading)
- **Choice:** Chris reads CORE's terms (https://core.ac.uk/terms, 3.1 and 3.2) as allowing free use by an individual working in a personal capacity who acknowledges CORE (https://core.ac.uk/acknowledge). CORE's use is kept narrow: the ~500-work validation sample and identifying each institution's repository. The site publishes only agreement rates and repository names, never CORE records, with the required acknowledgement.
- **Alternatives:** Contact CORE first; skip CORE.
- **Risk noted:** 3.1 applies only if the use is not in the section 3 "contact us" list, which includes products for everyone related to an "analytical dashboard," and that list applies "irrespective of" free-licence eligibility. A courtesy note to CORE (https://core.ac.uk/about#contact) would remove the doubt. Revisit before phase 6, when CORE is first used.

## 2026-11-15 — Python
- Python 3.15.2 installed by Chris. Pipeline targets Python 3.13+.

## 2026-11-15 — UConn Health roll-up method
- **Choice:** UConn's figures use `authorships.institutions.lineage:I140172145|I75929689`, which returns each work once.
- **Alternatives:** Rely on lineage alone.
- **Why:** In OpenAlex, UConn Health's lineage is only itself, not UConn, so the lineage filter alone would leave out 5,443 UConn Health articles and reviews from 2015–2025 (45,991 combined vs 40,548 UConn alone).

## 2026-11-15 — Keyless calls for phase 1
- **Choice:** Phase 1 ran without a key (keyless allowance is $0.10/day). Sorting by works count put every needed institution on the first page, so no paging was needed.
- **Why:** Lets phase 1 run before Chris has a key. Phase 2 needs a key for cursor paging.

## 2026-11-15 — Final institution list (phase 1 approved)
- **Choice:** The 15 named institutions (UConn Health rolled into UConn) plus the University of Bridgeport (I154300980) and the University of Saint Joseph (I192633058). 18 OpenAlex IDs, 17 reported institutions.
- **Alternatives:** Named list only; every CT college in OpenAlex.
- **Why:** Bridgeport and Saint Joseph each publish more than Western CSU and the Coast Guard Academy. The other 11 CT colleges in OpenAlex each have fewer than 50 articles and reviews over 2015–2025, and together would change statewide totals by less than 0.1%.

## 2026-11-15 — Universities only
- **Choice:** Only college and university affiliations count. Hospitals, health systems, research institutes, companies, and government bodies are out of scope (Yale New Haven Hospital, Hartford Hospital, Jackson Laboratory, CT Agricultural Experiment Station, etc.).
- **Why:** Chris's call. The project is about academic libraries' institutions. A hospital paper still counts when an author also lists one of the 16 institutions.

## 2026-11-15 — Raw cache compressed and kept outside OneDrive
- **Choice:** Raw API responses are gzip-compressed and stored in `C:/Users/chris/ct-oa-observatory-cache` (set by `RAW_DIR` in `.env`; default is `data/raw`).
- **Alternatives:** Uncompressed JSON in `data/raw` inside the project.
- **Why:** The full harvest is about 9 GB uncompressed (292 MB compressed). OneDrive would try to sync it. It is never committed either way.

## 2026-11-15 — Full author lists for large collaborations
- **Choice:** Re-fetch every work at the 100-author cap as a single record (free) and use that record.
- **Alternatives:** Accept the undercount; filter by institution separately per institution.
- **Why:** List results cap authorships at 100. Without the fix, 1,588 works lost their Connecticut affiliation and Yale was undercounted by 1,408. Details in docs/verification.md.

## 2026-11-15 — `apc_paid` not treated as an actual payment
- **Choice:** Use `apc_list` for estimates. Ignore `apc_paid` as evidence of payment.
- **Why:** OpenAlex gives no provenance for `apc_paid`, and it equals `apc_list` for 51,920 of 52,718 works where it is filled, so it is mostly the list price copied over.

## 2026-11-16 — Rule A: exclude repository records without a DOI (phase 2 approved)
- **Choice:** A work whose primary location is a repository and that has no DOI is excluded from every metric (1,827 works, 0.9%). It stays in the tables flagged `in_scope = false`, and the list is in `data/derived/quality/excluded_works.csv`.
- **Alternatives:** B, exclude only no-DOI records from Connecticut institutional repositories (720). C, keep everything with a note.
- **Why:** Chris's call. These are mostly repository-only records OpenAlex types as articles, such as student internship reflections and course projects in Digital Commons, plus PubMed stubs. The rule is simple to explain and leaves journal articles without DOIs alone (important for diamond and humanities journals). 193,734 works remain.

## 2026-11-16 — Metric definitions (phase 3)
- **Free to read** = any OA status except closed (diamond, gold, hybrid, bronze, green). Bronze counts because the article is readable at the publisher, though without an open license and possibly not permanently. The Methods page will say so.
- **Statewide without Yale** = works with at least one author at one of the 16 other institutions. A Yale-only paper drops out; a Yale-UConn paper stays. Alternative (drop every work with a Yale author) was rejected because it would remove UConn's and others' Yale collaborations.
- **APC estimates** count gold and hybrid works only, the statuses where an APC is normally charged. A missing list price is counted as unknown, not $0, and the number of works without a price is reported next to every estimate.
- **Publisher** = the top of OpenAlex's host organization lineage (e.g. Lippincott Williams & Wilkins rolls up to Wolters Kluwer), so imprints of one company are grouped.
- **Fields, topics, publishers** use 2015–2025 pooled. Top 10 by output and top 10 by closed works are both kept. Missing values are labeled "Unknown" so totals add up.
- **Green OA opportunity** moves to phase 6, where the brief places deposit policies and the OpenAlex-only proxy. It needs journal-level OpenAlex queries beyond this dataset.

## 2026-11-16 — "Without Yale" APC attribution uses non-Yale corresponding institutions only
- **Choice:** In the corresponding-author APC estimate for "statewide without Yale", a work counts only if a non-Yale Connecticut institution is corresponding.
- **Alternatives:** Keep "any Connecticut institution is corresponding" and relabel the figure.
- **Why:** The independent verification agent found 329 works (about $1.02M) where Yale was the only corresponding institution inside a figure labeled "without Yale". That contradicts the label, so the definition was fixed, not the label. See docs/verification-phase3.md.

## 2026-11-16 — Trinity / Washington College affiliation correction
- **Choice:** Remove a Trinity College credit when the raw affiliation text of the authors matched to Trinity names "Washington College" and never "Trinity" (`AFFILIATION_CORRECTIONS` in s04). 14 works in 2015–2025 and 2 in 2026. The rows stay in the tables, flagged `affiliation_corrected`.
- **Alternatives:** Leave OpenAlex's matching as is and note it as a limitation.
- **Why:** The error is systematic and identifiable. OpenAlex links authors at Washington College (Chestertown, Maryland) to Trinity, whose founding name was Washington College. It is 1.6% of Trinity's output. Yale's comparable noise (about 30 of 129,000 works) is too small to correct and is recorded as a limitation.

## 2026-11-16 — "Diamond" split by confirmed fee
- **Choice:** The site reports seven OA categories. OpenAlex's "diamond" is split in two:
  - **diamond**: OpenAlex says diamond and the recorded list fee is $0 (1,609 works statewide, 2015–2025).
  - **oa_fee_unconfirmed**, shown as "Open access journal, fee not confirmed": OpenAlex says diamond but no fee is recorded (9,183 works across all years) or the recorded fee is above $0 (19). Statewide 2015–2025 that is 8,349 works.
  - Both count as free to read. Neither is counted in APC estimates, which the Methods page will say. OpenAlex's own `oa_status` is kept unchanged in `works.parquet` for traceability. The site category is `oa_category` (s04 `oa_category()`).
- **Alternatives:** Keep OpenAlex's label with a Methods caveat. Wait for phase 6 DOAJ data.
- **Why:** Chris's call. OpenAlex labels an OA journal with no recorded fee as diamond, so only 16% of Connecticut's "diamond" works had a confirmed $0 fee. Some, such as Oncotarget, have charged fees. Phase 6 will use DOAJ data to move more works out of "fee not confirmed".
- **Effect:** Statewide 2015–2025, diamond goes from 5.7% to 0.9%, with 4.7% fee not confirmed. Free-to-read share is unchanged (66.81%).

## 2026-11-16 — Trend explanation corrected
- The 2023–2025 dip in free-to-read share is driven by **bronze** falling (15.9% to 8.1%), not green. Green is flat. Any site text must say this and call it a likely timing effect, to be retested with the next snapshot.

## 2026-11-16 — Site design: "research report" (replaces the Open Sun look)
- **Choice:** White page, Source Serif 4 headlines, Public Sans text and data, one reading column (44rem) with numbered figures ("Figure 1"), a dark red accent (#9b1c31 light, #f29aa8 dark), a statement headline built from the data ("Two-thirds of Connecticut's research is free to read"), and a "Key findings" box. Light and dark mode both supported.
- **Alternatives:** The first build reused Open Sun's cream and forest-green palette with Fraunces and Atkinson Hyperlegible. Chris rejected it (colors, fonts, layout and too similar to Open Sun). Three mockups on real data were compared: research report, civic data dashboard, academic library.
- **Why:** Chris's pick. It reads as authoritative and citable, suits readers new to open access, and its numbered figures map onto the Methods page and the phase 9 write-ups.
- **Headline wording:** shares are turned into words ("two-thirds", "three in five") only when within 1.5 points of the fraction (`inWords` in site/src/lib/format.ts); otherwise the exact percentage is used.

## 2026-11-16 — Chart palette (validated)
- **OA categories, light (on white):** diamond #1c5cab, fee not confirmed #3a9cc4, gold #a87700, hybrid #7a5cd6, bronze #b84f1b, green #0b7d56, closed #938f86. **Dark (on #15181d):** #4c7fe6, #26a9a0, #c98500, #9085e9, #d95926, #199e70, #c9c5ba. **Two-series lines:** #2a78d6 and #eb6834 (light), #3987e5 and #d95926 (dark).
- **How chosen:** the dataviz skill's validator. Every colored slot clears 3:1 against the page, every neighbouring pair in stack order clears the colorblind (CVD ΔE ≥ 8) and normal-vision (ΔE ≥ 15) checks, in both modes. Closed is a deliberate neutral gray, so the validator's "reads gray" flag on it is expected.
- **Adjustments made:** the first green and bronze sat at a lightness where neither white nor black text inside a bar reached 4.5:1 (axe flagged 25 labels). Green and bronze were darkened and closed lightened to keep the colorblind checks passing. Brief: "standard OA colors only where they pass contrast" is met. Every color passes, and colors are always paired with a legend, labels and a table.
- **No hover tooltips:** charts have no JavaScript. Hover tooltips built in CSS alone fail WCAG 1.4.13 (they can't be dismissed), so values come from in-bar labels, the legend, the written summary and the table view. Native `title` text gives mouse users segment values.

## 2026-11-16 — Site build tooling
- **Astro 7.4.7**, pinned exactly. 7.4.4 (the newest release older than two weeks) had a moderate security advisory fixed in 7.4.7, so the oldest patched release was used. Fonts and d3-dsv pinned to releases older than two weeks. axe-core 4.14.0 is a dev-only dependency for accessibility checks and is never shipped.
- **Astro telemetry disabled** on this machine (`astro telemetry disable`). Vercel and the GitHub Action need `ASTRO_TELEMETRY_DISABLED=1` set as an environment variable (phase 5 and 8).
- **Zero scripts** on every page; the only external reference is a plain link to OpenAlex.

## 2026-11-16 — No Open Sun reference on the site
- **Choice:** The site does not call itself a companion or sibling to Open Sun and does not link to it. The footer line was removed, and the planned About page will not link to Open Sun.
- **Why:** Chris's call. The project should stand on its own.

## 2026-11-16 — Publishing (phase 5)
- **Public repo:** https://github.com/HB-Papa/ct-oa-observatory (Chris approved public). Commits use the GitHub no-reply address.
- **Licenses:** MIT for code (`LICENSE`), CC0 for data (`data/derived/LICENSE.md`). Chris's choice.
- **Kept out of git:** `.env`, the raw cache (outside the project), `data/derived/*.parquet` (large and rebuilt by the pipeline; the site needs only the metric CSVs), `verification/affiliation_unconfirmed_samples.csv` (raw affiliation text with researchers' names and emails), and `docs/pitch.md` (Chris's full name; outreach text, kept local by Chris's choice). First-name references in the project records are published, as Chris approved.
- **Search indexing:** off (`noindex` meta tag plus an `X-Robots-Tag` header) until the Methods and Limitations page exists in phase 7, so the numbers are never found without their caveats. Chris's choice.
- **Security headers** (`site/vercel.json`): a Content Security Policy that blocks all scripts and outside connections (the site has none), plus no-referrer, nosniff, and a permissions policy that opts out of interest-based ad tracking.

## 2026-11-16 — Deployed to Vercel
- **Live:** https://ct-oa-observatory.vercel.app (Vercel project ct-oa-observatory, team hb-papa, root directory `site/`, Node 24, `ASTRO_TELEMETRY_DISABLED=1` for production and preview).
- **How:** deployed from this computer with `vercel deploy --prod`. Linking the GitHub repo for automatic deploys failed because Vercel's GitHub app does not yet have access to this repository (a GitHub account setting only Chris can change). `.vercelignore` keeps `.env`, `.env.local`, the venv, Parquet tables, the researcher-email file and the pitch out of any upload; the upload matched the public repo (84 files, 4 MB).
- **Checked live:** both pages return 200; CSP, no-referrer, nosniff, permissions policy and `X-Robots-Tag: noindex` present; no cookies; zero scripts; fonts load under the CSP; 0 requests to other servers.

## 2026-11-16 — Phase 6 cross-check design
- **Sample:** 510 articles with a DOI, 30 per institution, spread over 2015–2025, drawn by a fixed hash (`pipeline/s07_crosscheck_sample.py`) so reruns pick the same works. Equal per institution, not proportional, so small colleges are represented. Overall rates are unweighted sample rates and are labeled that way.
- **Alternatives:** a simple random sample of 500 (would be about 60% Yale, with almost nothing from the small colleges); stratifying by institution × year with equal cells (too few works in some cells).
- **Unpaywall** is used as a consistency check only. It now runs on the OpenAlex database, so agreement with it is expected and does not count as independent confirmation. The contact email is in `.env` only and replaced with EMAIL_REMOVED in the query log and cache file names (`pipeline/sources.py`).
- **OpenAIRE** is the main independent check. Queried without a token, 50 DOIs per request (11 requests, under the 60/hour anonymous limit), so no account was needed.
- **CORE:** not run yet. Chris emailed CORE on 2026-11-16 to confirm the licence. If there is no reply by the end of phase 7, CORE is skipped and the Methods page says why.

## 2026-11-16 — DOAJ results are reported separately, not applied (pending Chris)
- **Choice:** DOAJ's answer for the 8,349 "fee not confirmed" works is published as its own table (`crosschecks/doaj_fee_unconfirmed.csv`). The site's category figures stay OpenAlex-only for now.
- **Alternatives:** move works DOAJ confirms as fee-free into "diamond" and works DOAJ lists with a fee into "gold" on the site.
- **Why:** CLAUDE.md says never blend validation-source numbers into OpenAlex figures. Applying DOAJ would do exactly that. It is Chris's call whether this enrichment is worth an exception (it would be labeled).
- **Rule used:** DOAJ shows a journal's current policy, so a work only gets a DOAJ answer if it was published in or after the journal's open access start year (`oa_start`).

## 2026-11-16 — OpenAPC compared in euros, against today's list price
- **Choice:** compare fees paid (OpenAPC, euros incl. VAT) with the journal's euro list price in OpenAlex. Two views: the same Connecticut articles where a co-author's institution reported the payment, and the same journals (median paid per journal, at least 5 payments since 2015).
- **Alternatives:** convert euros to dollars at historical exchange rates (adds a second source and an assumption).
- **Why:** comparing in one currency needs no conversion. Because list prices are today's prices, the gap includes price rises over time, which is what the Methods page needs to show ("older years may be overstated").
- **License:** the per-article match table is an adapted OpenAPC database, so it is published under ODbL in its own folder. Summary figures carry the ODbL attribution line.
- **Library-funded journals:** 55 works with no author fee (mostly SCOAP3 high-energy physics journals) have an OpenAPC payment because a library reports its consortium share per article. They stay in "no author fee"; the Methods page explains it.

## 2026-11-16 — Green OA proxy definition
- **Choice:** a journal "shows deposit evidence" if at least 3 of its articles (2015–2025, worldwide) are green with an accepted manuscript as the best free copy, in a repository other than PubMed Central or Europe PMC. A Connecticut article is a repository candidate if it is closed or bronze, has no free repository copy, and its journal shows deposit evidence.
- **Alternatives:** count PubMed Central deposits (rejected: most follow funder mandates such as NIH's, which publishers accept only for funded articles); a threshold of 1 (a single deposit can be a mistake or a special case) or 10 (misses smaller journals). Results for 1 and 10 are kept in the metric file as a sensitivity check.
- **Cost:** one OpenAlex `group_by` request per 100 journals, 101 requests for 10,045 journals.
- **Candidate list:** `data/derived/downloads/repository_candidates.csv`, no author names, not shown on the site, as the brief requires.
- **Tightened after the cross-check agent's report:** a candidate must have no free copy anywhere except the publisher's page (the first version only excluded accepted or published repository copies, so 2,676 bronze works with free preprints slipped in), and meeting abstracts in journal supplements are left out by DOI pattern (`suppl` DOIs and Blood's ASH abstract DOIs). Statewide candidates: 43,581 (24.7% of 2015–2025 articles); 25,612 at threshold 10, 55,728 at threshold 1.
- **Not changed (Chris to decide):** meeting abstracts stay in the main OA figures for now. Dropping them would remove about 1,000 closed works statewide (a lower bound) and is a scope change.
