# Connecticut Open Access Observatory

How much of the research published by Connecticut's colleges and universities can anyone read for free, and how much is still behind a paywall?

This project answers that for 17 Connecticut institutions, 2015 to 2025, using the open database [OpenAlex](https://openalex.org/). It has two parts:

- **A data pipeline** (`pipeline/`, Python) that downloads the records from OpenAlex, checks them, and computes every number shown on the site.
- **A website** (`site/`, Astro) that presents the results with written summaries and data tables for every chart, built to WCAG 2.2 AA with no tracking.

Status: work in progress. The Overview and one institution profile are built. Methods, data downloads, cross-checks with other sources, and the remaining profiles come next.

## What's here

| Folder | What it holds |
|---|---|
| `pipeline/` | One script per step. `python -m pipeline.run_all` runs them all. |
| `data/derived/metrics/` | The published numbers, as CSV files (CC0). |
| `data/derived/quality/` | Data quality checks, including the list of excluded records. |
| `data/logs/query_log.csv` | Every OpenAlex query the pipeline made, with its cost. |
| `docs/` | API notes, cost estimate, data quality report, verification reports. |
| `verification/` | An independent recomputation of the key figures, written separately from the pipeline. |
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

A full harvest costs about 2,000 OpenAlex credits, well inside the free daily allowance. A plain-language guide for librarians with no coding background will replace this section before launch.

## License

Code: MIT (see `LICENSE`). Data in `data/derived/`: CC0 (see `data/derived/LICENSE.md`). Source data: OpenAlex, CC0.
