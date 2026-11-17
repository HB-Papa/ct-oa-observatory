"""Monthly refresh: compare the new figures with the last published ones.

Plain-language summary: after the monthly rerun, this script reads the newly
built metric files and the previous version from git, and checks that nothing
moved in a way that suggests a broken harvest rather than real change. If a
check fails it exits with an error, so the GitHub Action stops and nothing is
published. If all checks pass it writes a short report and adds an entry to
the site's changelog with the new headline figures.

Checks (thresholds are deliberately loose; real month-to-month change is small):
- Harvest complete: every institution-year downloaded matches OpenAlex's own
  count within 0.5% (institution-years with at least 20 works).
- Statewide articles 2015-2025 change between -2% and +5% (indexing mostly adds).
- Statewide share free to read moves by at most 3 percentage points.
- No institution with at least 200 articles loses more than 10% of them, and no
  institution's share free to read moves by more than 8 points.

Usage: python -m pipeline.refresh_report [--baseline GIT_REF]   (default HEAD)
Writes data/logs/refresh_report.md, and site/src/lib/changelog.json when the
snapshot date changed and every check passed.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

import pandas as pd

from pipeline.config import DERIVED, LOGS, ROOT

MET = "data/derived/metrics"
CHANGELOG = ROOT / "site" / "src" / "lib" / "changelog.json"


def old_csv(ref: str, name: str) -> pd.DataFrame:
    text = subprocess.run(["git", "show", f"{ref}:{MET}/{name}"], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout
    return pd.read_csv(io.StringIO(text))


def old_json(ref: str, name: str) -> dict:
    return json.loads(subprocess.run(["git", "show", f"{ref}:{MET}/{name}"], cwd=ROOT, capture_output=True,
                                     text=True, encoding="utf-8", check=True).stdout)


def checks(old: pd.DataFrame, new: pd.DataFrame, comp: pd.DataFrame) -> list[tuple[str, bool, str]]:
    out = []
    big = comp[comp.group_by_count >= 20]
    worst = (big["diff"].abs() / big.group_by_count).max() if len(big) else 0
    out.append(("Harvest matches OpenAlex counts (each institution-year within 0.5%)", worst <= 0.005,
                f"largest gap {worst:.2%}"))
    o, n = old.set_index("entity"), new.set_index("entity")
    ch = n.loc["statewide", "works"] / o.loc["statewide", "works"] - 1
    out.append(("Statewide articles change between -2% and +5%", -0.02 <= ch <= 0.05, f"{ch:+.2%}"))
    d = n.loc["statewide", "free_to_read_share"] - o.loc["statewide", "free_to_read_share"]
    out.append(("Statewide share free to read moves 3 points or less", abs(d) <= 0.03, f"{d * 100:+.1f} points"))
    keys = [k for k in o.index if k in n.index and not k.startswith("statewide") and o.loc[k, "works"] >= 200]
    drops = {k: n.loc[k, "works"] / o.loc[k, "works"] - 1 for k in keys}
    worst_k = min(drops, key=drops.get)
    out.append(("No institution loses more than 10% of its articles", drops[worst_k] >= -0.10,
                f"largest drop {worst_k} {drops[worst_k]:+.1%}"))
    moves = {k: n.loc[k, "free_to_read_share"] - o.loc[k, "free_to_read_share"] for k in keys}
    worst_m = max(moves, key=lambda k: abs(moves[k]))
    out.append(("No institution's share moves more than 8 points", abs(moves[worst_m]) <= 0.08,
                f"largest move {worst_m} {moves[worst_m] * 100:+.1f} points"))
    return out


def report(old_snap: str, new_snap: str, old: pd.DataFrame, new: pd.DataFrame, results) -> str:
    o, n = old.set_index("entity"), new.set_index("entity")
    lines = [f"# Data refresh: {old_snap} to {new_snap}", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |" for name, ok, detail in results]
    lines += ["", "| Entity | Articles before | Articles after | Free to read before | after |", "|---|---:|---:|---:|---:|"]
    for k in n.index:
        if k in o.index:
            lines.append(f"| {n.loc[k, 'entity_name']} | {o.loc[k, 'works']:,} | {n.loc[k, 'works']:,} | "
                         f"{o.loc[k, 'free_to_read_share']:.1%} | {n.loc[k, 'free_to_read_share']:.1%} |")
    return "\n".join(lines) + "\n"


def add_changelog(new_snap: str, old: pd.DataFrame, new: pd.DataFrame) -> None:
    o, n = old.set_index("entity"), new.set_index("entity")
    entries = json.loads(CHANGELOG.read_text(encoding="utf-8"))
    if any(e.get("snapshot") == new_snap for e in entries):
        return
    entries.insert(0, {
        "date": new_snap, "snapshot": new_snap, "title": "Monthly data refresh",
        "items": [
            f"Figures now use OpenAlex data downloaded on {new_snap}.",
            f"Statewide share free to read, 2015 to 2025: {n.loc['statewide', 'free_to_read_share']:.1%} "
            f"(was {o.loc['statewide', 'free_to_read_share']:.1%}). Articles counted: "
            f"{n.loc['statewide', 'works']:,} (was {o.loc['statewide', 'works']:,}).",
            f"Without Yale: {n.loc['statewide_no_yale', 'free_to_read_share']:.1%} "
            f"(was {o.loc['statewide_no_yale', 'free_to_read_share']:.1%}).",
        ],
    })
    CHANGELOG.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="HEAD")
    args = ap.parse_args()
    old = old_csv(args.baseline, "free_to_read_2015_2025.csv")
    new = pd.read_csv(DERIVED / "metrics" / "free_to_read_2015_2025.csv")
    old_snap = old_json(args.baseline, "manifest.json")["snapshot_date"]
    new_snap = json.loads((DERIVED / "metrics" / "manifest.json").read_text(encoding="utf-8"))["snapshot_date"]
    comp = pd.read_csv(DERIVED / "quality" / "completeness_by_institution_year.csv")
    results = checks(old, new, comp)
    text = report(old_snap, new_snap, old, new, results)
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "refresh_report.md").write_text(text, encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text)
    print(text)
    if not all(ok for _, ok, _ in results):
        sys.exit("Refresh checks failed: nothing will be published.")
    if new_snap != old_snap:
        add_changelog(new_snap, old, new)
        print("Changelog entry added.")


if __name__ == "__main__":
    main()
