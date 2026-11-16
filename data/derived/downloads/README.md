# Repository candidates (for librarians)

`repository_candidates.csv` lists Connecticut articles that are closed or bronze, have no free copy in OpenAlex other than the publisher's own page (no free preprint either), are not meeting abstracts, and were published in a journal that shows deposit evidence. One row per institution and article, so a co-authored article appears once for each Connecticut institution. 2015 to 2026. Rows with `year_complete` false are from 2026, which is still being indexed.

**This is a proxy, not a policy check.** "Deposit evidence" means at least 3 articles in the journal (2015 to 2025, worldwide) are free only through an accepted manuscript in a repository other than PubMed Central or Europe PMC. Confirm the publisher's current policy and any embargo before depositing. The list is meant for planning outreach. It is not shown on the website and names no authors.

Built by `pipeline/s12_green_proxy.py` from OpenAlex. License CC0 1.0.

| Column | Meaning |
|---|---|
| institution, institution_key | Connecticut institution the article is credited to |
| openalex_id | OpenAlex work ID |
| doi | DOI link |
| title | Article title |
| year, year_complete | Publication year, and whether that year is complete (2015 to 2025) |
| journal, publisher | Journal and top-level publisher in OpenAlex |
| current_status | OpenAlex OA status today: closed or bronze (bronze is free to read at the publisher but without an open license and possibly not permanently) |
| journal_deposit_evidence_articles | Number of evidence articles in this journal (higher means stronger evidence) |
