# API notes: data sources for the Connecticut Open Access Observatory

Checked: 2026-11-15. Every fact below comes from the official documentation page listed under each source, read on that date, or from a small public test request (noted "tested live"). Anything I could not confirm from an official page is marked **UNCONFIRMED**.

How to read this file: each source has the same headings. "Key" means a password-like code a service gives you so it knows who is asking. "Rate limit" means how many requests you may send in a given time. "License" means what we are allowed to do with the data, especially whether we can republish our own tables built from it.

---

## 1. OpenAlex

**What it is:** A free, open catalog of scholarly works, authors, journals and institutions, run by the nonprofit OurResearch. This will be our main source.

**Base URL:** `https://api.openalex.org`

Old documentation sites `docs.openalex.org` and `developers.openalex.org` now redirect (permanently) to `https://help.openalex.org/`.

**Authentication (keys)**
- A key is **not strictly required**, but in practice we need one. Without a key:
  - all keyless users on the same internet address (IP) share one daily budget of $0.10 (tested live: the API itself says so in its response);
  - you can only fetch the **first page** of any result list. Following to page 2 with "cursor paging" returns an error (401). That means at most 10,000 results per query.
- **Confirmed: cursor paging past the first page requires a key.**
- How the key is sent: either as a URL parameter `?api_key=YOUR_KEY` or as the header `Authorization: Bearer YOUR_KEY`. The docs say both work the same way.
- **Confirmed: the old "polite pool" / `mailto=` email parameter is gone.** The deprecations page says the system "has been replaced by API keys" and that `mailto` is now ignored (this change happened before February 2026).
- **How to get a key:** create a free account at openalex.org/signup, then copy the key from Settings > API key (openalex.org/settings/api-key). There is also an automated route: send your email address to `https://api.openalex.org/api-keys`, then click the link OpenAlex emails you. **We did not do either; the project owner must do this.**

**Rate limits (speed)**
- No key: 10 requests per second.
- Free key or prepaid usage: 30 requests per second.
- Annual plan: 50 requests per second.
- Semantic search: 1 request per second for everyone.
- Going over your daily budget returns error 429 ("too many requests").

**Costs and billing: confirmed usage-based billing**
- OpenAlex describes itself as "data is free, service is sold." You pay for API usage beyond a free daily allowance.
- **Free daily allowance with a free key: $1.00 per day = 10,000 credits.** (1 credit = $0.0001.) The budget resets at midnight UTC (7 p.m. or 8 p.m. Connecticut time, depending on daylight saving).
- Without a key: $0.10 per day = 1,000 credits, shared by everyone on your IP address.
- **Confirmed: new accounts are slowed down until their first $1 of usage.** The first $1 is released at up to $0.10 every 5 minutes, so about 50 minutes of steady use. After that the slowdown ends. It does not apply to annual plans, prepaid usage, organization keys, or accounts created before 3 November 2026.
- Pay-as-you-go: prepaid in $1 steps, used only after the free daily budget runs out, and expires 3 months after your most recent purchase. No payment card is needed for the free tier.
- Annual plans (for reference only): Member $5,000/yr ($20/day budget); Member+ $10,000/yr ($100/day, plus daily sync of the full database); Partner from $20,000/yr ($200+/day).
- You can check usage in response headers (`X-RateLimit-Remaining`, `X-RateLimit-Credits-Used`, etc.), at `https://api.openalex.org/rate-limit?api_key=...`, or on the dashboard at openalex.org/settings/usage. You can also ask `/query` what a query would cost before running it (free).

**Cost per call (from the "Example costs" page; key items tested live where noted)**

| Kind of request | Credits per call | Dollars per 1,000 calls |
|---|---|---|
| Single record by ID or DOI (e.g. `/works/doi:10.xxx`) | 0 (free) | free. Tested live: 0 credits, even with `select=` |
| List with filters (one page of results) | 1 | $0.10. Tested live: 1 credit |
| `group_by` on a filtered list | 1 | $0.10. Tested live: 1 credit |
| `group_by` on a search | 10 | $1.00 |
| Keyword search (`search=` or any `.search` filter) | 10 | $1.00 |
| Semantic search | 10 | $1.00 |
| Reranked search | 20 | $2.00 |
| Cached PDF download | 100 | $10.00 |

- **Cursor paging:** the docs do not list a separate price. Each cursor page appears to be billed like any other list page (1 credit for filters, 10 for a search). **UNCONFIRMED** (no page says this explicitly).
- **`per_page`:** the docs do not say it changes the per-call price. They do say that `per_page=100` (the supported maximum; 200 still works but is deprecated) "stretches your budget," because you get more records for the same call. In other words, cost is per call, not per record.
- **`select=`:** no page says it changes cost. Our live test showed a single-record call with `select=` still cost 0. **UNCONFIRMED for list calls**, but there is no sign it matters.
- What $1/day buys: roughly 10,000 filtered list pages (up to 1,000,000 records at 100 per page), or 1,000 searches. Single-record lookups are unlimited.
- The docs' own example: downloading all of Harvard's ~870,000 works costs about $0.87. A Connecticut-wide pull should fit within a few days of free budget, or cost a few dollars.

**Terms of use and data license**
- **CC0** (public domain). The pricing page says every record is released under CC0, with no "personal use only" exception. We may republish derived data freely.
- Attribution is not legally required, but OpenAlex asks to be cited: Priem, J., Piwowar, H., & Orr, R. (2022). *OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts.* arXiv. https://arxiv.org/abs/2205.01833

**Fields we need on the Work record (all confirmed in docs; most also tested live)**

| Field | Status | Notes |
|---|---|---|
| `open_access.oa_status` | Confirmed | Values: `diamond`, `gold`, `green`, `hybrid`, `bronze`, `closed`. **Yes, "diamond" is a value**: a fully OA journal that charges no APC. |
| `open_access.any_repository_has_fulltext` | Confirmed | True if any repository holds a free copy. Shows green copies that `oa_status` hides (e.g. a gold article also deposited in a repository). |
| `open_access.is_oa`, `open_access.oa_url` | Confirmed | |
| `locations[].version` | Confirmed | `publishedVersion`, `acceptedVersion`, `submittedVersion`, or null. Each location also has `is_oa`, `license`, `landing_page_url`, `pdf_url`, `is_accepted`, `is_published`, and `source.type` (tested live: `journal` or `repository`). |
| `apc_list` | Confirmed | `value`, `currency`, `value_usd`. The journal's advertised price. A value of 0 means a diamond journal. |
| `apc_paid` | Confirmed, **but has no `provenance` field** | `value`, `currency`, `value_usd` only. The docs say outright that "no field says which of the two a value came from," so we cannot tell whether a figure came from OpenAPC or is a list-price estimate. Tested live: no provenance key. |
| `corresponding_institution_ids` | Confirmed | Institutions of the corresponding author(s). If no author is marked corresponding but all authors share one institution, that institution is used. |
| `authorships[].institutions[]` | Confirmed | Each has `id`, `display_name`, `ror`, `country_code`, `type`, `lineage`. Also `authorships[].countries`, `is_corresponding`, `raw_affiliation_strings`. |
| Filter `authorships.institutions.lineage` | Confirmed and tested live | Counts a parent institution together with its sub-units, e.g. `filter=authorships.institutions.lineage:I32971472` (Yale). |
| `primary_topic` | Confirmed | Top topic with its subfield, field and domain, or null. |
| `type` | Confirmed | One type per work (list below). |
| `is_retracted` | Confirmed | True or false. |

**Paratext:** now flagged by `type = paratext` (covers, tables of contents, author guidelines and similar). The old `is_paratext` true/false field still exists but is deprecated. Filter with `type:paratext` (or `type:!paratext` to exclude).

**Work `type` values (25):** article, book, book-chapter, book-review, conference-abstract, conference-paper, data-paper, dataset, dissertation, editorial, erratum, letter, other, paratext, peer-review, preprint, reference-entry, report, retraction, review, software, software-paper, standard, study-registration, supplementary-materials. Notes: `study-registration` was added 7 Nov 2026 and records are still being moved into it. `libguides` was removed on 7 Nov 2026 (filtering on it now errors). Several new types have little or no data yet.

**`group_by` limits:** up to 200 groups per page. Use cursor paging for more (needs a key; groups then come back sorted by name, not by count). Up to 3 fields can be grouped at once. Unknown values are hidden unless you add `:include_unknown`. `meta.groups_count` counts only the current page.

**Finding Connecticut institutions:** Institution records have a `geo` block (`city`, `region`, `country_code`, latitude/longitude) and support a `geo.region` filter. **Tested live:** `/institutions?filter=country_code:US,geo.region:Connecticut` returns 488 institutions, led by Yale and UConn. Institutions also have `lineage`, `ror`, `type` and a `repositories` list (repositories the institution hosts). Works records do not carry the state, so the method is: (1) list Connecticut institutions, then (2) filter works by those institution IDs.

**Other changes worth knowing:** `host_venue` was removed (use `primary_location`). Concepts are deprecated (use Topics). `volume` was removed on 14 Nov 2026 (use `parent_works`). `select=` works only on top-level fields (e.g. `select=open_access`, not `open_access.is_oa`).

**Pages used (all checked 2026-11-15)**
- https://help.openalex.org/ (and redirects from https://developers.openalex.org/ and https://docs.openalex.org/)
- https://help.openalex.org/llms.txt
- https://help.openalex.org/access/
- https://help.openalex.org/access/pricing/
- https://help.openalex.org/access/example-costs/
- https://help.openalex.org/api/authentication/
- https://help.openalex.org/api/deprecations/
- https://help.openalex.org/api/paging/
- https://help.openalex.org/api/grouping/
- https://help.openalex.org/api/selecting-fields/
- https://help.openalex.org/data/works/attributes/
- https://help.openalex.org/data/works/open-access/
- https://help.openalex.org/data/work-types/
- https://help.openalex.org/data/locations/
- https://help.openalex.org/data/authorships/
- https://help.openalex.org/data/institutions/
- https://help.openalex.org/access/unpaywall/
- https://help.openalex.org/how-to/citing-openalex/
- Live test requests (keyless, 4 total): `/institutions?filter=country_code:US,geo.region:Connecticut`, `/works/doi:10.1371/journal.pone.0266781?select=...` (twice), `/works?filter=authorships.institutions.lineage:I32971472,publication_year:2024&group_by=open_access.oa_status`

---

## 2. Jisc Open Policy Finder (replaces Sherpa Romeo)

**What it is:** A UK service, run by Jisc, that records each journal's policy on what authors may deposit in repositories (which version, where, after what embargo).

**Base URL:** `https://api.openpolicyfinder.jisc.ac.uk`. Main endpoint: `/retrieve`. There are also "retrieve by ID" and "object IDs" endpoints.

**Authentication:** A key is required, sent in the request header `x-api-key` (not in the URL, unlike the old Sherpa API). Tested live: a request without a key is refused (403).

**History:** The new platform launched 11 Feb 2026. The old Sherpa Services API was due to be switched off at the end of April 2026, later extended to the end of July 2026. Existing keys were migrated automatically.

**Are new key requests open? UNCONFIRMED, but probably yes.**
- The 11 Feb 2026 and 7 May 2026 notices said new key requests were paused during the migration (which ended end of July 2026).
- Search-engine copies of the "How to request a new API key" page showed a line saying "We are currently NOT accepting requests for new API keys until ... the end of July 2026." **That line is no longer on the live page** (checked 2026-11-15). However, no news item announces that requests have reopened (the latest news item, 13 Aug 2026, does not mention the API).

**How a person requests a key (current page):** send an email to help@jisc.ac.uk with the subject line "Open policy finder API request." Include your name, email address, organisation, and the purpose you will use the API/data for. Say whether you want to join their mailing list. There is no web form and no self-service account.

**Rate limits:** not stated on any page. **UNCONFIRMED.**

**Costs:** none mentioned. The API is described as free for non-commercial use. **UNCONFIRMED** whether any fee exists.

**License and terms: problem for us**
- The data is licensed **CC BY-NC-ND 4.0** (Attribution, NonCommercial, NoDerivatives). The key request page says the API "is for non-commercial use."
- "NoDerivatives" is the issue: strictly read, it bars sharing adapted versions of the data. Publishing our own table of "journal X allows accepted-manuscript deposit after 12 months" could count as an adaptation. Attribution is also required, and non-commercial terms apply. **We cannot republish Open Policy Finder-derived data under CC0.** See "Conflicts and flags" below.
- The site's "using our content" page could not be found (404), so detailed reuse terms beyond the licence statement are **UNCONFIRMED**.

**Looking up a journal by ISSN**
- `GET https://api.openpolicyfinder.jisc.ac.uk/retrieve?item-type=publication&format=Json&filter=[["issn","equals","1932-6203"]]` with header `x-api-key: YOUR_KEY`.
- `issn` is a listed filter field for publications. The field name is confirmed in the filter table. **This exact URL was not tested** because we have no key.
- Filters are a JSON list of up to three `[field, operator, value]` triples, combined with AND. Operators: `equals`, `contains word`, `gte`, `lte`.
- `limit` max 100. Use `offset` for up to 10,000 records, or `search_after` beyond that. Responses are always JSON with `items`, `next_search_after`, `totalHits`.

**Deposit permission fields (from the metadata schema page)**
Publication records contain `publisher_policy`, and each policy has a list `permitted_oa`. Each `permitted_oa` entry has:
- `article_version`: `submitted`, `accepted`, or `published`. For the accepted manuscript, look for `accepted`.
- `location.location`: where you may deposit (e.g. institutional repository; `this_journal` means the OA journal itself).
- `embargo`: `amount` (a number) plus `units` (`days`, `weeks`, `months`, `years`).
- `license`, `conditions`, `copyright_owner`, `additional_oa_fee` (yes/no), `prerequisites`, `public_notes`.
- `publisher_policy.permitted_oa`-level summary fields `open_access_prohibited` and `permitted_oa` (yes/no) also appear in the schema. Most coded fields have a `*_phrases` companion with plain-English wording.

**Pages used (checked 2026-11-15)**
- https://openpolicyfinder.jisc.ac.uk/help/developers
- https://openpolicyfinder.jisc.ac.uk/help/developers/how-to-access-the-api-platform
- https://openpolicyfinder.jisc.ac.uk/help/developers/how-to-request-a-new-api-key
- https://openpolicyfinder.jisc.ac.uk/help/developers/api-types
- https://openpolicyfinder.jisc.ac.uk/help/developers/api-types/object-retrieval-api
- https://openpolicyfinder.jisc.ac.uk/help/developers/metadata-schema
- https://openpolicyfinder.jisc.ac.uk/whats-new (list), /whats-new/11-02-2026, /whats-new/07-05-2026, /whats-new/13-08-2026
- One keyless test request to `/retrieve` (refused with 403, as expected)

---

## 3. Unpaywall

**What it is:** A database of free, legal copies of articles, looked up by DOI. Run by OurResearch, the same nonprofit as OpenAlex.

**Important: Unpaywall now runs on OpenAlex data.** OpenAlex's help pages say Unpaywall was moved "onto the OpenAlex database" in late 2025. It is now an old-style view of the same data: its `is_oa`, `oa_status` and best link match OpenAlex's `open_access` and best location. **For our project, Unpaywall adds nothing that OpenAlex lacks.** Use OpenAlex directly; use Unpaywall only as a cross-check or if a tool requires it.

**Base URL:** `https://api.unpaywall.org/v2/{DOI}?email=YOUR_EMAIL`

**Authentication:** no key. **An email address is still required** as the `email` parameter. Tested live: no email returns "Email address required in API call," and a placeholder address (example.com) is rejected with "Please use your own email address." (We did not send a real address.) A key exists only for the paid Data Feed.

**Rate limit:** 100,000 calls per day. This figure comes from a search-engine summary of the official API page and from an Unpaywall staff post. The official page itself (unpaywall.org/products/api) is a JavaScript app that our tools could not read. **Treat as UNCONFIRMED from the live official page.**

**Costs:** REST API free. The Data Feed (bulk) is paid. OpenAlex suggests feed subscribers talk to sales about moving to OpenAlex.

**Fields (from Unpaywall's data-format page, via search summaries)**
- `oa_status`: gold, hybrid, bronze, green, closed. **UNCONFIRMED** whether Unpaywall now also reports `diamond` as OpenAlex does.
- `best_oa_location`: the single best free copy.
- `oa_locations[]`: all free copies, each with `host_type` (`publisher` or `repository`), `version` (`submittedVersion`, `acceptedVersion`, `publishedVersion`), `license`, `url`, `url_for_pdf`, `evidence`.
- `z_authors` is deprecated (use OpenAlex `authorships`). `oa_date` is now just the publication date, not the date a copy became free.
- These field definitions could not be read directly from the official page (JavaScript-only). **Partly UNCONFIRMED.**

**License:** Unpaywall data has historically been released as CC0. **UNCONFIRMED** from a live official page today. Since the data is now the OpenAlex data, which is confirmed CC0, the risk is low.

**Pages used (checked 2026-11-15)**
- https://help.openalex.org/access/unpaywall/ (official, readable)
- https://unpaywall.org/products/api, https://unpaywall.org/data-format, https://unpaywall.org/api/v2 (official but JavaScript-only, not readable by our tools)
- Web search results summarizing those pages, plus https://groups.google.com/g/unpaywall/c/zFDeIdXC5lE (staff post on the 100k/day limit)
- Two live test requests to `api.unpaywall.org/v2/...` (no email; placeholder email)

---

## 4. OpenAIRE Graph API

**What it is:** A European open-science graph that links publications, datasets, repositories, funders and organisations. It is especially strong on repository (green) copies.

**Base URL:** `https://api.openaire.eu/graph/`. There are two query styles: **V4** (filter-based, recommended for new work) and V3 (older, kept for compatibility).

**Research product by DOI (V4):**
`GET https://api.openaire.eu/graph/v4/research-products?filter=ids.doi:10.1371/journal.pone.0266781`
Tested live: works without a key and returns one record.

**Authentication and rate limits**
- No key needed for basic use. Docs: **60 requests per hour** without a token, **7,200 per hour** with one.
- Note: our keyless live test returned a header `x-ratelimit-limit: 7199`, higher than the documented 60/hour. The actual keyless limit is **UNCONFIRMED**; plan for 60/hour.
- Tokens: register a free OpenAIRE account at https://services.openaire.eu/uoa-user-management/register.jsp, then get a personal access token from your account's token page. The token lasts 1 hour (refresh tokens are available). **Not registered.**
- Offset paging is capped at 10,000 results per query.

**Costs:** free ("free for any third-party service to use").

**How open access and repository copies are expressed**
- Record-level: `bestAccessRight` (COAR access-rights code and label, e.g. `c_abf2` / `OPEN`), `openAccessColor` (`gold`, `hybrid`, `bronze`), `isGreen` (true/false), `isInDiamondJournal` (true/false), `publiclyFunded`.
- `instances[]`: each copy of the work (publisher or repository), with `accessRight` (code, label, `openAccessRoute`), `hostedby` (the source holding the copy, e.g. a repository), `collectedfrom`, `license`, `refereed`, `type`, `urls`, `pids`, and `articleProcessingCharge` (amount and currency).
- V4 filters: `best_oa.rights` (Open Access, Embargo, Restricted, Closed Access, ...), `oa_color`, `is_green`, `is_in_diamond_journal`, `host_datasource.id`, `authorships.countries`, `authorships.institutions.ror`.
- The full list of allowed `openAccessRoute` values is **UNCONFIRMED** (the docs show only the example `gold`).

**License and attribution**
- The Graph is **CC BY** ("due to some input sources whose license is CC-BY"). The docs add that "parts of the graphs can be re-used as CC-0," but do not say which parts. The CC BY version number is **UNCONFIRMED** (not stated).
- Commercial and non-commercial reuse is allowed **if OpenAIRE is credited as the data source**.
- Requested citation: "OpenAIRE Research Graph Dataset," Zenodo, DOI 10.5281/zenodo.3516917.

**Pages used (checked 2026-11-15)**
- https://graph.openaire.eu/docs/apis/graph-api/
- https://graph.openaire.eu/docs/apis/graph-api-v4/
- https://graph.openaire.eu/docs/apis/graph-api-v4/research-products/
- https://graph.openaire.eu/docs/apis/graph-api-v4/research-products/filter-syntax/
- https://graph.openaire.eu/docs/data-model/entities/research-product/
- https://graph.openaire.eu/docs/apis/terms/
- https://graph.openaire.eu/docs/license/
- https://graph.openaire.eu/docs/downloads/full-graph (citation, via search summary)
- One live keyless request (DOI lookup above)

---

## 5. CORE API (v3)

**What it is:** A UK aggregator (The Open University) that harvests full texts and metadata from repositories worldwide. Useful for finding which repositories exist and what they hold.

**Base URL:** `https://api.core.ac.uk/v3/`

**Authentication:** A key is optional for basic use. CORE says the API "is free and requires no authentication." The key is sent as the header `Authorization: Bearer YOUR_KEY`. Register for a key on https://core.ac.uk/services/api (enter an email address; the key is emailed). **Not registered.**

**Rate limits (CORE counts "tokens": a simple query = 1 token, complex ones 3 to 5)**

| User type | Limit |
|---|---|
| No key | **100 tokens per day**, max 10 per minute. No full text. |
| Registered personal | 1,000 tokens/day, max 25/min |
| Registered academic, institution not a CORE member | 5,000 tokens/day, max 10/min |
| Registered academic at a Supporting/Sustaining member, or organisations | about 200,000 tokens/day |

Without a key the API is too limited for anything beyond spot checks. Even 5,000/day is small for checking every Connecticut DOI one at a time.

**Costs:** basic access is free. Faster organisational access "is typically not free." There is a 30-day free trial for institutions and enterprises. Whether our use qualifies for a free licence is **UNCONFIRMED** (see terms).

**Endpoints we would use**
- Search works by DOI: `https://api.core.ac.uk/v3/search/works/?q=doi:"10.1038/s41597-023-02208-w"` (also `/v3/search/outputs/?q=doi:"..."` for individual repository copies).
- Data providers (repositories) by country: `https://api.core.ac.uk/v3/search/data-providers/?q=location.countryCode:us`
- Data providers by institution: `?q=institutionName:Basel`, or by OpenDOAR ID: `?q=openDoarId:1275`. Records include `dataProviderLocation` (countryCode, countryName), `institutionName`, `rorId`, `openDoarId`, `urlHomepage`.
- For Connecticut: search `location.countryCode:us AND institutionName:"Yale"` (and so on for each institution), or match on `rorId` against OpenAlex institution ROR IDs. There is no state field. **UNCONFIRMED** whether a state/region filter exists; none is documented.
- Rate-limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Retry-After`.

**Terms of use and license: restrictive**
- CORE keeps "sui generis database rights" (a European database right). Using the API requires a **licence**, which many users can get free.
- Free licence for a public research organisation (e.g. a university) applies **if** the work produces "a research paper or a publicly available report" **and** you acknowledge CORE (https://core.ac.uk/acknowledge).
- You **must contact CORE** if your product "is intended for the benefit of everyone but related to the functionality provided by one of CORE's existing services, such as ... search, discovery system or analytical dashboard." A public OA dashboard plausibly falls under this.
- The downloadable ODC-By datasets can be used commercially or non-commercially with acknowledgement. ODC-By requires attribution, so it is not CC0.
- CORE says it is reviewing its licensing and plans to release factual metadata as CC0 or ODC-0 in future. **Not yet in effect.**
- **Bottom line:** we should not republish CORE-derived data as CC0 without written permission from CORE.

**Pages used (checked 2026-11-15)**
- https://api.core.ac.uk/docs/v3 (read via direct download; WebFetch was blocked with 403)
- https://core.ac.uk/services/api (same)
- https://core.ac.uk/terms (same)

---

## 6. DOAJ (Directory of Open Access Journals)

**What it is:** The authoritative list of vetted fully open access journals, including whether each charges an APC.

**Current version:** API v4 (v4.0.0, with the minor update v4.0.1 on 21 Aug 2025). Base URL: `https://doaj.org/api/`

**Journal search by ISSN:** `GET https://doaj.org/api/search/journals/issn:1932-6203`. Tested live: works without a key.

**Authentication:** none needed for reading/searching. Keys are mainly for publishers uploading data.

**Rate limits:** 2 requests per second on all routes. Bursts of up to 5 are queued if the average stays at 2/second.

**Costs:** free.

**APC fields (tested live):** `bibjson.apc.has_apc` (true/false), `bibjson.apc.max` (a list of `{price, currency}`), and `bibjson.apc.url`. Also useful: `bibjson.deposit_policy` (`has_policy`, `service`, e.g. "Open Policy Finder", plus `url`), `bibjson.license`, `bibjson.waiver`, `bibjson.other_charges`. Exact field names other than `apc` and `deposit_policy` were not individually tested. **Partly UNCONFIRMED.**

**License: changed. Journal metadata is now CC0.**
- The terms page today says: "The journal-level metadata is available with a CC0 waiver," and article metadata is also CC0. (Older DOAJ statements, e.g. a 2020 blog post, said journal metadata was CC BY-SA 4.0; that is no longer the case.)
- The DOAJ website's own text/content (not the metadata) is CC BY-SA 4.0. That does not affect data we pull through the API.
- No attribution is required, though crediting DOAJ is good practice.

**Pages used (checked 2026-11-15)**
- https://doaj.org/docs/api/
- https://doaj.org/api/docs
- https://doaj.org/terms
- One live request: `https://doaj.org/api/search/journals/issn:1932-6203`

---

## 7. OpenAPC

**What it is:** A dataset of APC amounts that institutions actually paid, reported by the institutions themselves. Coordinated from Bielefeld University Library, Germany.

**Where to get it:** GitHub repository https://github.com/OpenAPC/openapc-de (no API and no key).
- Article APCs: `data/apc_de.csv` (direct download: https://raw.githubusercontent.com/OpenAPC/openapc-de/master/data/apc_de.csv, about 67 MB, about 270,000 rows, periods up to 2026).
- Transformative-agreement articles: in `data/transformative_agreements/` (articles under such agreements are kept out of the APC file).
- Book processing charges: `data/bpc.csv`. Extra costs (page/colour charges): `data/additional_costs.csv`.
- Institution list: `data/institutions.csv` (with ROR IDs, continent, country, state).

**Columns in `apc_de.csv` (header read live):** institution, period, euro, doi, is_hybrid, opt_out, publisher, journal_full_title, issn, issn_print, issn_electronic, issn_l, license_ref, indexed_in_crossref, pmid, pmcid, ut, url, doaj, agreement, group_id. All the columns we expected are present, plus `opt_out`, `agreement` and `group_id`.

**Currency:** euros (`euro` column), including VAT.

**License: not CC0**
- Data: **Open Database License (ODbL 1.0)**. Individual contents: Database Contents License (DbCL 1.0). The README text is CC BY 4.0.
- ODbL requires **attribution** and **share-alike**: if we publicly use an adapted database built from OpenAPC, that adapted database must also be offered under ODbL. See "Conflicts and flags."

**US and Connecticut institutions:** Only 6 US institutions report: Harvard (94 rows), Virginia Tech (321), University of Rhode Island (44), IUPUI (116), Thomas Jefferson University (157), and the Bill & Melinda Gates Foundation (12,407). **No Connecticut institution reports.** There is no Yale, UConn, Wesleyan or any other CT entry, and no row mentions Yale, Connecticut or Wesleyan. OpenAPC will only help as a price benchmark (e.g. average paid APC per journal), not as a record of Connecticut spending.

**Note:** OpenAlex's `apc_paid` already uses OpenAPC values where they exist, but without saying which values came from OpenAPC (see section 1).

**Pages used (checked 2026-11-15)**
- https://github.com/OpenAPC/openapc-de (README, License section)
- https://raw.githubusercontent.com/OpenAPC/openapc-de/master/README.md
- https://raw.githubusercontent.com/OpenAPC/openapc-de/master/data/institutions.csv (downloaded and searched)
- https://raw.githubusercontent.com/OpenAPC/openapc-de/master/data/apc_de.csv (downloaded, searched, then deleted)

---

## (a) Keys the user needs

| Source | Key needed? | How to get it | Cost |
|---|---|---|---|
| OpenAlex | **Yes** (in practice: needed for paging past the first page and for a personal $1/day budget) | Free account at openalex.org/signup, then Settings > API key | Free up to $1/day (10,000 credits). Beyond that, prepaid in $1 steps. New accounts are paced for the first $1 (about 50 minutes). |
| Jisc Open Policy Finder | **Yes** (every request) | Email help@jisc.ac.uk, subject "Open policy finder API request," with name, email, organisation, intended use. Whether requests are open again after the 2026 pause is UNCONFIRMED. | Free (non-commercial); no fee mentioned |
| Unpaywall | No key, but **a real email address** in every request | n/a | Free (100,000/day, partly UNCONFIRMED) |
| OpenAIRE Graph | Optional (60/hour without, 7,200/hour with) | Register at services.openaire.eu, then create a personal access token (expires hourly) | Free |
| CORE | Optional, but effectively needed (only 100 tokens/day without) | Enter email at core.ac.uk/services/api; possibly a licence conversation with CORE (see flags) | Free for eligible academic use; organisational/faster plans "typically not free" |
| DOAJ | No | n/a | Free |
| OpenAPC | No (CSV download from GitHub) | n/a | Free |

## (b) Conflicts and flags (licenses that could block republishing derived data as CC0)

1. **Jisc Open Policy Finder: CC BY-NC-ND 4.0. Biggest problem.** "NoDerivatives" means we may not share adapted versions, and "NonCommercial" plus attribution also apply. Publishing per-journal deposit rules, or per-article "could have been deposited" flags derived from them, under CC0 is not allowed. Options: ask Jisc for written permission; publish only aggregate counts with attribution and get Jisc's view on whether that counts as a derivative; or keep OPF-derived fields out of the CC0 release.
2. **OpenAPC: ODbL 1.0 (attribution + share-alike).** Any public dataset that includes adapted OpenAPC data must itself be ODbL, not CC0. This matters little, since there are no Connecticut rows. Using OpenAPC only for internal benchmarking, or releasing that part separately under ODbL, avoids the clash.
3. **CORE: database rights plus licence required; dashboards need permission.** CORE's terms say to contact them if building something like a "search, discovery system or analytical dashboard." Republishing CORE-derived data as CC0 needs CORE's written OK. Their bulk datasets are ODC-By (attribution required). CORE plans to move factual metadata to CC0/ODC-0, but this has not happened yet.
4. **OpenAIRE Graph: CC BY (version unstated).** Attribution is required ("crediting OpenAIRE as the data source"). Facts like "this DOI is green OA" are arguably not copyrightable, but to be safe, OpenAIRE-derived fields should carry a CC BY attribution, or be released under CC BY rather than CC0. The docs say parts are CC0 but do not say which.
5. **Unpaywall: license not confirmed on a live page today** (historically CC0, now the same data as OpenAlex). Low risk, but prefer OpenAlex as the source of record.
6. **No conflict:** OpenAlex (CC0) and DOAJ (CC0 for both journal and article metadata, changed from the older CC BY-SA statement).
7. **Related non-license flag:** OpenAlex `apc_paid` mixes reported (OpenAPC) values and list-price estimates with no provenance field, so "APC paid" figures must be labelled as estimates.

## (c) Future sources (not researched in depth)

- **BASE (Bielefeld Academic Search Engine):** large repository aggregator with good US repository coverage. Could help find green copies OpenAlex misses, but its API needs IP allow-listing on request and overlaps heavily with OpenAlex/CORE. Moderate value.
- **Semantic Scholar:** adds its own OA PDF links and citation data. Little extra for OA status beyond OpenAlex. Its license (ODC-By for datasets, plus API terms) is not CC0. Low value.
- **Crossref:** the original source for DOIs, licences, funders and some publisher APC data. OpenAlex already includes most of it. Useful only to double-check licence URLs or to get data straight from the source. Low to moderate value.
- **Preprint servers (arXiv, bioRxiv/medRxiv, SSRN, OSF):** OpenAlex already indexes these as `type: preprint` locations. Querying them directly adds little except fresher data. Low value.
