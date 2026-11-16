"""Step 2b: turn cached OpenAlex pages into tidy Parquet tables.

Reads only the cache written by s03 (no API calls, no credits). Writes:
- data/derived/works.parquet              one row per work
- data/derived/work_institutions.parquet  one row per work x reported institution
- data/derived/work_locations.parquet     one row per place a copy of the work lives
Works at the 100-author cap use the full single-record response from s03b.
No author names or author IDs are kept: the site reports institutions only.
"""
from __future__ import annotations

import re

import pandas as pd

from pipeline.config import DERIVED, snapshot
from pipeline.institutions import ID_TO_KEY
from pipeline.s03_harvest_works import YEARS, pages
from pipeline.s03b_fetch_full_authorships import AUTHOR_CAP, full_record


def short(oid):
    return oid.rsplit("/", 1)[-1] if oid else None


def inst_keys(inst: dict) -> set[str]:
    """Reported institutions an affiliation belongs to, via its lineage."""
    ids = {short(i) for i in (inst.get("lineage") or [])} | {short(inst.get("id"))}
    return {ID_TO_KEY[i] for i in ids if i in ID_TO_KEY}


# Known OpenAlex affiliation errors, corrected here (approved 2026-11-16).
# (institution key, pattern for the wrong place, pattern for the right place).
# A credit is removed when the raw affiliation strings of the authors matched to
# that institution name the wrong place at least once and never name the right one.
# Trinity College was founded as "Washington College" (1823); OpenAlex matches
# authors at Washington College in Chestertown, Maryland, to Trinity.
AFFILIATION_CORRECTIONS = [
    ("trinity", r"washington college", r"trinity"),
]


def corrected_out(key: str, raw_strings: list[str]) -> bool:
    """True if this institution credit is a known affiliation error."""
    for k, wrong, right in AFFILIATION_CORRECTIONS:
        if (k == key and any(re.search(wrong, x, re.I) for x in raw_strings)
                and not any(re.search(right, x, re.I) for x in raw_strings)):
            return True
    return False


def oa_category(oa_status: str | None, apc_list_usd) -> str | None:
    """The OA category reported on the site (approved 2026-11-16).

    Same as OpenAlex's oa_status, except "diamond" is split. OpenAlex labels an
    article diamond when its journal is open access and OpenAlex has no fee on
    record, not only when the fee is known to be $0. So:
      diamond             OpenAlex says diamond AND the recorded list fee is $0
      oa_fee_unconfirmed  OpenAlex says diamond but no fee is recorded, or the
                          recorded fee is above $0 (contradictory)
    Both are free to read. Neither is counted in APC estimates."""
    if oa_status == "diamond":
        return "diamond" if apc_list_usd == 0 else "oa_fee_unconfirmed"
    return oa_status


def exclude_reason(primary_is_repository: bool, doi) -> str | None:
    """Rule A (approved 2026-11-16): a work whose primary location is a repository
    and that has no DOI is not counted. These are mostly repository-only records
    (student work, course projects, PubMed stubs) that OpenAlex types as articles.
    Journals without DOIs are not affected. Excluded works stay in the tables,
    flagged, so the exclusion can be counted and reported."""
    if primary_is_repository and not doi:
        return "repository_record_no_doi"
    if is_meeting_abstract(doi):
        return "meeting_abstract"
    return None


# Meeting abstracts (approved by Chris 2026-11-16). Conference abstracts printed
# in journal supplements are typed "article" (sometimes "review") in OpenAlex.
# They are short, almost never open, and not research articles, so they are not
# counted. Matched by DOI pattern for the journals that publish them in bulk.
# A broad "suppl" match was rejected: it also catches real articles in
# supplement issues (e.g. Oceanography, Tobacco Regulatory Science).
MEETING_ABSTRACT_DOI_PATTERNS = [
    r"10\.1212/wnl\..*_supplement",                    # Neurology (AAN annual meeting)
    r"10\.1096/fasebj\..*_supplement",                 # The FASEB Journal (Experimental Biology)
    r"10\.1200/jco\..*_suppl",                         # Journal of Clinical Oncology (ASCO)
    r"10\.1161/[a-z]+\.[0-9]+\.suppl_",                # AHA journals: Circulation, Stroke, Hypertension, Circ Res
    r"10\.1182/blood-20[0-9]{2}-[0-9]{5,6}$",          # Blood, ASH abstracts 2019 on (articles have a month: blood-2016-09-...)
    r"10\.1182/blood\.v[0-9]+\.2[23]\.[0-9]+\.[0-9]+$",  # Blood, ASH abstract issues 2015-2016
    r"10\.1254/jpssuppl\.",                            # Japanese Pharmacological Society meeting proceedings
    r"10\.1556/jba\.[0-9]+\.[0-9]+\.suppl",            # Journal of Behavioral Addictions conference abstract book
]
_MEETING_ABSTRACT_RE = re.compile("|".join(MEETING_ABSTRACT_DOI_PATTERNS), re.I)


def is_meeting_abstract(doi) -> bool:
    return bool(doi) and bool(_MEETING_ABSTRACT_RE.search(doi))


def flatten(w: dict, snap: str):
    wid = short(w["id"])
    oa = w.get("open_access") or {}
    pl = w.get("primary_location") or {}
    src = pl.get("source") or {}
    host_lineage = src.get("host_organization_lineage_names") or []
    topic = w.get("primary_topic") or {}
    apc_list = w.get("apc_list") or {}
    apc_paid = w.get("apc_paid") or {}
    corr = {short(i) for i in (w.get("corresponding_institution_ids") or [])}

    # Map every affiliation on the work to our institution keys, and note which
    # of our institutions appear among the corresponding institutions.
    keys, corr_keys, any_id_to_keys, raw = set(), set(), {}, {}
    for a in w.get("authorships") or []:
        for inst in a.get("institutions") or []:
            k = inst_keys(inst)
            keys |= k
            any_id_to_keys[short(inst.get("id"))] = k
            for key in k:
                raw.setdefault(key, []).extend(a.get("raw_affiliation_strings") or [])
    corrected = {k for k in keys if corrected_out(k, raw.get(k, []))}
    valid_keys = keys - corrected
    for cid in corr:
        corr_keys |= any_id_to_keys.get(cid, set()) | ({ID_TO_KEY[cid]} if cid in ID_TO_KEY else set())

    locs = []
    for i, loc in enumerate(w.get("locations") or []):
        s = loc.get("source") or {}
        locs.append({
            "work_id": wid, "location_index": i, "is_primary": loc.get("id") == pl.get("id"),
            "source_id": short(s.get("id")), "source_name": s.get("display_name"),
            "source_type": s.get("type"), "source_host_name": s.get("host_organization_name"),
            "version": loc.get("version"), "is_oa": loc.get("is_oa"),
            "license": loc.get("license"), "landing_page_url": loc.get("landing_page_url"),
        })
    repo = [l for l in locs if l["source_type"] == "repository"]

    work = {
        "work_id": wid, "doi": w.get("doi"), "title": w.get("title"),
        "publication_year": w.get("publication_year"), "publication_date": w.get("publication_date"),
        "type": w.get("type"), "language": w.get("language"),
        "oa_status": oa.get("oa_status"), "is_oa": oa.get("is_oa"),
        "oa_category": oa_category(oa.get("oa_status"), apc_list.get("value_usd")),
        "any_repository_has_fulltext": oa.get("any_repository_has_fulltext"),
        "source_id": short(src.get("id")), "source_name": src.get("display_name"),
        "source_type": src.get("type"), "source_issn_l": src.get("issn_l"),
        "source_is_in_doaj": src.get("is_in_doaj"), "source_is_oa": src.get("is_oa"),
        "publisher_id": short(src.get("host_organization")),
        "publisher_name": src.get("host_organization_name"),
        "publisher_parent_name": host_lineage[-1] if host_lineage else src.get("host_organization_name"),
        "primary_version": pl.get("version"), "primary_license": pl.get("license"),
        "apc_list_usd": apc_list.get("value_usd"), "apc_paid_usd": apc_paid.get("value_usd"),
        "n_corresponding_institutions": len(corr),
        "topic_id": short(topic.get("id")), "topic_name": topic.get("display_name"),
        "subfield_name": (topic.get("subfield") or {}).get("display_name"),
        "field_name": (topic.get("field") or {}).get("display_name"),
        "domain_name": (topic.get("domain") or {}).get("display_name"),
        "n_authorships": len(w.get("authorships") or []),
        "n_reported_institutions": len(valid_keys),
        "primary_is_repository": src.get("type") == "repository",
        "has_repository_location": bool(repo),
        "has_oa_accepted_repository_copy": any(l["version"] == "acceptedVersion" and l["is_oa"] for l in repo),
        "has_oa_published_repository_copy": any(l["version"] == "publishedVersion" and l["is_oa"] for l in repo),
        "snapshot_date": snap,
    }
    work["exclude_reason"] = exclude_reason(work["primary_is_repository"], work["doi"])
    if work["exclude_reason"] is None and keys and not valid_keys:
        work["exclude_reason"] = "affiliation_correction_no_ct_institution"
    work["in_scope"] = work["exclude_reason"] is None
    # Corrected credits keep their row (so counts can be reconciled with OpenAlex)
    # but are flagged and left out of every metric.
    wi = [{"work_id": wid, "institution_key": k, "publication_year": work["publication_year"],
           "is_corresponding_institution": k in corr_keys,
           "affiliation_corrected": k in corrected,
           "in_scope": work["in_scope"] and k not in corrected}
          for k in sorted(keys)]
    return work, wi, locs


def main():
    snap = snapshot()["snapshot_date"]
    works, wis, locs, seen = [], [], [], set()
    for year in YEARS:
        for body in pages(year):
            for w in body["results"]:
                wid = short(w["id"])
                if wid in seen:  # a work can only appear once, but check anyway
                    continue
                seen.add(wid)
                if len(w.get("authorships") or []) >= AUTHOR_CAP:
                    w = full_record(wid)  # list results cap authors at 100; use the full record
                a, b, c = flatten(w, snap)
                works.append(a); wis.extend(b); locs.extend(c)
        print(f"{year}: {len(works):,} works so far", flush=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(works).to_parquet(DERIVED / "works.parquet", index=False)
    pd.DataFrame(wis).to_parquet(DERIVED / "work_institutions.parquet", index=False)
    pd.DataFrame(locs).to_parquet(DERIVED / "work_locations.parquet", index=False)
    print(f"works {len(works):,}, work_institutions {len(wis):,}, locations {len(locs):,}")


if __name__ == "__main__":
    main()
