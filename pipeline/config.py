"""Shared settings: folders, snapshot date, years, and work types.

Plain-language summary: every script imports this file so they all agree on
where data lives and which years and work types count.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DATA = ROOT / "data"
# Cached API responses, never committed. Defaults to data/raw. Set RAW_DIR in .env
# to keep the cache somewhere else (the full harvest is about 1 GB compressed,
# too large for a OneDrive-synced folder).
RAW = Path(os.getenv("RAW_DIR") or DATA / "raw")
DERIVED = DATA / "derived"      # tidy tables that are published
LOGS = DATA / "logs"            # query log, committed so every number is traceable
SNAPSHOT_FILE = DATA / "snapshot.json"

COMPLETE_YEARS = (2015, 2025)   # last complete year is 2025
INCOMPLETE_YEAR = 2026          # shown separately, labeled incomplete
CORE_TYPES = ("article", "review")
BOOK_TYPES = ("book", "book-chapter")  # reported as a separate count only


def snapshot() -> dict:
    """Return the current snapshot, creating one dated today if none exists.

    A snapshot ties every cached response and table to one harvest date.
    Start a new one with `python -m pipeline.new_snapshot`.
    """
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    return new_snapshot()


def new_snapshot() -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    snap = {"snapshot_date": dt.date.today().isoformat()}
    SNAPSHOT_FILE.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return snap
