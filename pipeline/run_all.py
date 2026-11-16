"""Run the whole pipeline in order: python -m pipeline.run_all

Each step can also be run alone (python -m pipeline.<step>). Steps that call
OpenAlex read from the cache when a response is already saved for the current
snapshot, so rerunning costs nothing. Start a fresh harvest with
python -m pipeline.new_snapshot first.
"""
import importlib
import time

STEPS = [
    ("s01_institutions_list", "List Connecticut institutions in OpenAlex"),
    ("s02_institution_counts", "Count works per institution (group_by)"),
    ("s03_harvest_works", "Download in-scope works, one year at a time"),
    ("s03b_fetch_full_authorships", "Fetch full author lists for large collaborations"),
    ("s04_build_tables", "Build tidy Parquet tables"),
    ("s05_quality_report", "Write the data quality report"),
    ("s06_metrics", "Compute published metrics"),
]

if __name__ == "__main__":
    for module, label in STEPS:
        t = time.time()
        print(f"\n=== {module}: {label}", flush=True)
        importlib.import_module(f"pipeline.{module}").main()
        print(f"=== {module} finished in {time.time() - t:.0f}s", flush=True)
