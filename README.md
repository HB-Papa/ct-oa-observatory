# Connecticut Open Access Observatory

How much of the research published by Connecticut's colleges and universities can anyone read for free, and how much is still behind a paywall?

**Website: https://ct-oa-observatory.vercel.app**

This project answers that for 17 Connecticut institutions, 2015 to 2025, using the open database [OpenAlex](https://openalex.org/). It has two parts:

- **A data pipeline** (`pipeline/`, Python) that downloads the records from OpenAlex, checks them, and computes every number shown on the site.
- **A website** (`site/`, Astro) that presents the results with written summaries and data tables for every chart, built to WCAG 2.2 AA with no tracking and no JavaScript.

## For librarians: using the data without code

You do not need to run anything to use the results.

1. **Read the figures** on the website: an overview, a profile for each of the 17 institutions, and a Compare page.
2. **Download the tables** from the [Downloads page](https://ct-oa-observatory.vercel.app/downloads/). They are plain CSV files that open in Excel, Google Sheets, R, Tableau or Power BI. Each file's columns are explained on that page and in `data-dictionary.csv`.
3. **Plan repository outreach** with `repository_candidates.csv`: closed or bronze articles from your institution, in journals where other authors have deposited accepted manuscripts. Filter on `institution_key` for your institution. It is a starting point, not a permissions check: confirm each publisher's policy and embargo before depositing. It names no authors.
4. **Check the methods** on the [Methods page](https://ct-oa-observatory.vercel.app/methods/) before quoting a number. Fee figures are estimates from listed prices, and repository candidates are a proxy.

Spotted something wrong, such as a repository copy OpenAlex missed or an article credited to the wrong institution? Please open an issue on GitHub.

## What's here

| Folder | What it holds |
|---|---|
| `pipeline/` | One script per step. `python -m pipeline.run_all` runs them all. |
| `data/derived/metrics/` | The published numbers, as CSV files (CC0). |
| `data/derived/downloads/` | The repository candidate list for librarians (CC0). |
| `data/derived/crosschecks/` | Comparisons with Unpaywall, OpenAIRE, DOAJ and OpenAPC (licenses differ by file; see its `LICENSE.md`). |
| `data/derived/quality/` | Data quality checks, including the list of excluded records. |
| `data/logs/query_log.csv` | Every query the pipeline made, with its cost. |
| `docs/` | API notes, cost estimate, data quality report, verification, cross-check and accessibility reports. |
| `verification/` | An independent recomputation of the key figures, written separately from the pipeline, and the cross-check scripts. |
| `tests/` | Known-answer tests for the counting and metric rules (`pytest`). |
| `site/` | The website. |
| `DECISIONS.md` | Every methodological choice, the alternatives, and why. |

## Rerunning it

You need Python 3.13 or newer and a free OpenAlex API key.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # on Mac or Linux: .venv/bin/pip
cp .env.example .env                            # then put your OpenAlex key in .env
python -m pipeline.run_all
python -m pytest
```

`python -m pipeline.run_all --crosschecks` also reruns the checks against other sources. Unpaywall needs a contact email (`UNPAYWALL_EMAIL` in `.env`), which is removed from every saved log.

A full harvest costs about 2,000 OpenAlex credits, well inside the free daily allowance. Every response is saved, so rerunning from the saved data costs nothing.

To build the website: `cd site`, `npm install`, `npm run build`. It reads the CSVs in `data/derived/`.

## License

Code: MIT (see `LICENSE`). Data in `data/derived/`: CC0 (see `data/derived/LICENSE.md`), except cross-check files built from OpenAIRE (CC BY 4.0) and OpenAPC (ODbL 1.0). Source data: OpenAlex, CC0.
