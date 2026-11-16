"""Small OpenAlex client with a permanent cache and a query log.

What it does, in plain language:
- Every request is saved to data/raw/openalex/<snapshot date>/ the first time.
  Asking the same question again in the same snapshot reads the saved file
  instead of calling the API, so nothing is downloaded (or paid for) twice.
- Every request, cached or not, is written to data/logs/query_log.csv with the
  URL (key removed), whether it came from the cache, and the credits OpenAlex
  reported spending. That log is how each number traces back to a query.
- The API key is read from .env and never written to disk or the log.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import threading
import json
import os
import time
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from pipeline.config import LOGS, RAW, ROOT, snapshot

BASE = "https://api.openalex.org"
load_dotenv(ROOT / ".env")
_LOG_LOCK = threading.Lock()
_SESSION = requests.Session()
API_KEY = os.getenv("OPENALEX_API_KEY", "").strip()
LOG_FIELDS = ["logged_at", "snapshot_date", "script", "url", "from_cache",
              "status", "credits_used", "cost_usd", "remaining_usd", "cache_file"]


def build_url(path: str, params: dict) -> str:
    """URL without the key. Parameters are sorted so the same question always
    produces the same URL and therefore the same cache file."""
    query = urlencode(sorted((k, v) for k, v in params.items() if v is not None), safe=":,|<>!")
    return f"{BASE}/{path.lstrip('/')}" + (f"?{query}" if query else "")


def _cache_path(url: str):
    snap = snapshot()["snapshot_date"]
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return RAW / "openalex" / snap / f"{digest}.json.gz"


def _read_cache(path):
    """Read a cached response. Older phase 1 files are uncompressed .json."""
    plain = path.with_suffix("")  # strips .gz
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
    if plain.exists():
        return json.loads(plain.read_text(encoding="utf-8"))
    return None


def _log(row: dict) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / "query_log.csv"
    new = not path.exists()
    with _LOG_LOCK, path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def get(path: str, params: dict, script: str, log_cache_hits: bool = True) -> dict:
    """Fetch one OpenAlex response, from the cache if we already have it."""
    url = build_url(path, params)
    cache = _cache_path(url)
    row = {"logged_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "snapshot_date": snapshot()["snapshot_date"], "script": script, "url": url,
           "cache_file": "raw/" + cache.relative_to(RAW).as_posix()}
    cached = _read_cache(cache)
    if cached is not None:
        if log_cache_hits:
            _log(row | {"from_cache": True, "status": "cached", "credits_used": 0})
        return cached["body"]

    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    for attempt in range(5):
        resp = _SESSION.get(url, headers=headers, timeout=180)
        if resp.status_code != 429 and resp.status_code < 500:
            break
        time.sleep(float(resp.headers.get("Retry-After", 2 ** attempt)))
    h = resp.headers
    row |= {"from_cache": False, "status": resp.status_code,
            "credits_used": h.get("X-RateLimit-Credits-Used"),
            "cost_usd": h.get("X-RateLimit-Cost-USD"),
            "remaining_usd": h.get("X-RateLimit-Remaining-USD")}
    _log(row)
    resp.raise_for_status()
    body = resp.json()
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(json.dumps(
        {"url": url, "fetched_at": row["logged_at"], "body": body}).encode("utf-8"), 6))
    tmp.replace(cache)  # write-then-rename, so an interrupted run never leaves half a file
    return body
