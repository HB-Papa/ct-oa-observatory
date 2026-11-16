"""Cached client for the validation sources (Unpaywall, OpenAIRE, DOAJ, OpenAPC, CORE).

Plain-language summary: works like pipeline/openalex.py. Every response is
saved once under RAW/<source>/<snapshot date>/ and read from there next time,
and every request is written to data/logs/query_log.csv.

Privacy: Unpaywall needs a contact email in each request. The email lives only
in .env. It is replaced with EMAIL_REMOVED before the URL is logged, and the
cache file name is made from that cleaned URL, so the address never reaches
anything that is committed.
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import threading
import time
from urllib.parse import urlencode

import requests

from pipeline.config import RAW, snapshot
from pipeline.openalex import _log  # same query log file and columns

UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "").strip()
SECRETS = [s for s in (UNPAYWALL_EMAIL, os.getenv("CORE_API_KEY", "").strip()) if s]
USER_AGENT = "ct-oa-observatory/1.0 (https://github.com/HB-Papa/ct-oa-observatory)"

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = USER_AGENT
_LAST_CALL: dict[str, float] = {}
_LOCK = threading.Lock()


def scrub(text: str) -> str:
    """Remove the email (and any key) from a URL or message before it is saved."""
    for s in SECRETS:
        text = text.replace(s, "EMAIL_REMOVED").replace(s.replace("@", "%40"), "EMAIL_REMOVED")
    return text


def build_url(base: str, params: dict | None) -> str:
    if not params:
        return base
    return base + "?" + urlencode(sorted((k, v) for k, v in params.items() if v is not None), safe=":,|/")


def _cache_path(source: str, clean_url: str):
    digest = hashlib.sha1(clean_url.encode("utf-8")).hexdigest()[:16]
    return RAW / source / snapshot()["snapshot_date"] / f"{digest}.json.gz"


def get_json(source: str, base: str, params: dict | None, script: str,
             min_interval: float = 0.0, ok_statuses=(200,), headers: dict | None = None):
    """Fetch JSON from a validation source, from the cache if we have it.

    Returns (status, body). A 404 from Unpaywall means "DOI not known" and is
    cached like any other answer, so it is not asked again.
    """
    url = build_url(base, params)
    clean = scrub(url)
    cache = _cache_path(source, clean)
    row = {"logged_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "snapshot_date": snapshot()["snapshot_date"], "script": script, "url": clean,
           "cache_file": "raw/" + cache.relative_to(RAW).as_posix()}
    if cache.exists():
        saved = json.loads(gzip.decompress(cache.read_bytes()).decode("utf-8"))
        return saved["status"], saved["body"]

    for attempt in range(6):
        with _LOCK:  # simple politeness delay per source
            wait = _LAST_CALL.get(source, 0) + min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            _LAST_CALL[source] = time.monotonic()
        try:
            resp = _SESSION.get(url, timeout=120, headers=headers or {})
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            time.sleep(float(resp.headers.get("Retry-After", 2 ** attempt + 1)))
            continue
        break
    else:
        _log(row | {"from_cache": False, "status": "failed"})
        raise RuntimeError(f"{source}: no answer for {clean}")

    _log(row | {"from_cache": False, "status": resp.status_code})
    if resp.status_code not in ok_statuses:
        raise RuntimeError(f"{source}: HTTP {resp.status_code} for {clean}: {scrub(resp.text[:300])}")
    try:
        body = resp.json()
    except ValueError:
        body = {"_text": resp.text}
    body_text = scrub(json.dumps({"url": clean, "status": resp.status_code,
                                  "fetched_at": row["logged_at"], "body": body}))
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(body_text.encode("utf-8"), 6))
    tmp.replace(cache)
    return resp.status_code, json.loads(body_text)["body"]


def get_file(source: str, url: str, name: str, script: str):
    """Download a whole file once (used for the OpenAPC CSV). Returns its path."""
    path = RAW / source / snapshot()["snapshot_date"] / name
    row = {"logged_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "snapshot_date": snapshot()["snapshot_date"], "script": script, "url": url,
           "cache_file": "raw/" + path.relative_to(RAW).as_posix()}
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with _SESSION.get(url, stream=True, timeout=600) as resp:
        _log(row | {"from_cache": False, "status": resp.status_code})
        resp.raise_for_status()
        tmp = path.with_suffix(".tmp")
        with tmp.open("wb") as f:
            for chunk in resp.iter_content(1 << 20):
                f.write(chunk)
    tmp.replace(path)
    return path
