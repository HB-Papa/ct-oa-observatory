"""Phase 6, step 6: green OA opportunity (OpenAlex-only proxy).

Plain-language summary: a closed or bronze article could often be made
permanently free by depositing the author's accepted manuscript in a
repository. Whether the publisher allows that is a policy question, and the
policy database (Open Policy Finder) is licensed CC BY-NC-ND, which clashes
with releasing our data as CC0. So we use a proxy built only from OpenAlex:

  A journal "shows deposit evidence" if, in 2015-2025, at least 3 of its
  articles worldwide were free only through an accepted-manuscript copy in a
  repository other than PubMed Central or Europe PMC.

PubMed Central and Europe PMC are left out because those deposits mostly
follow funder mandates (such as NIH's), which publishers must accept for
funded articles only. They say little about whether any author may deposit.

A Connecticut article is a "repository candidate" if it is closed or bronze,
has no free copy anywhere except the publisher's own page (no free preprint
either), is not a meeting abstract, and its journal shows deposit evidence.
This is a proxy, not a policy check, and is labeled that way everywhere.

Cost: one OpenAlex group_by request per 100 journals (about 103 credits).

Outputs:
- data/derived/metrics/green_opportunity_2015_2025.csv  (per institution and statewide)
- data/derived/crosschecks/green_proxy_journals.csv     (evidence count per journal)
- data/derived/downloads/repository_candidates.csv      (article list for librarians; not shown on the site)
"""
from __future__ import annotations

import csv

import duckdb

from pipeline.config import COMPLETE_YEARS, CORE_TYPES, DERIVED, INCOMPLETE_YEAR
from pipeline.institutions import INSTITUTIONS, NAMES
from pipeline.openalex import get

SCRIPT = "s12_green_proxy"
LO, HI = COMPLETE_YEARS
TYPES = ",".join(f"'{t}'" for t in CORE_TYPES)
THRESHOLD = 3
FUNDER_REPOSITORIES = ["S2764455111", "S4306400806"]  # PubMed Central, Europe PMC
W = f"'{DERIVED / 'works.parquet'}'"
WI = f"'{DERIVED / 'work_institutions.parquet'}'"
WL = f"'{DERIVED / 'work_locations.parquet'}'"
# Meeting abstracts printed in journal supplements are typed "article" in
# OpenAlex. Nobody deposits them, so they are left out of the candidate list.
# Caught by DOI pattern ("suppl" DOIs, and Blood's ASH abstract DOIs); this is
# a lower bound, since abstracts without such a DOI are not caught.
MEETING_ABSTRACT = ("(lower(coalesce(w.doi,'')) like '%suppl%' "
                    r"or regexp_matches(lower(coalesce(w.doi,'')), '10\.1182/blood-20[0-9]{2}-[0-9]{5,6}$'))")
# Candidate: closed or bronze, no free copy anywhere except the publisher's own
# page (so no free preprint, accepted or published copy in any repository,
# including copies OpenAlex files under a journal by mistake), and not a
# meeting abstract.
CANDIDATE = (f"w.oa_category in ('closed','bronze') and not {MEETING_ABSTRACT} "
             f"and w.work_id not in (select work_id from {WL} where is_oa and not is_primary)")


def evidence_filter(ids: list[str]) -> str:
    return (f"primary_location.source.id:{'|'.join(ids)},publication_year:{LO}-{HI},type:article|review,"
            "oa_status:green,best_oa_location.version:acceptedVersion,best_oa_location.source.type:repository,"
            + ",".join(f"best_oa_location.source.id:!{r}" for r in FUNDER_REPOSITORIES))


def journal_evidence(ids: list[str]) -> dict[str, int]:
    counts = {i: 0 for i in ids}
    for k in range(0, len(ids), 100):
        chunk = ids[k:k + 100]
        body = get("works", {"filter": evidence_filter(chunk), "group_by": "primary_location.source.id"}, SCRIPT)
        if len(body["group_by"]) > len(chunk):
            raise RuntimeError("unexpected groups")
        for g in body["group_by"]:
            sid = g["key"].split("/")[-1]
            if sid in counts:
                counts[sid] = g["count"]
    return counts


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    con = duckdb.connect()
    ids = [r[0] for r in con.execute(f"""select distinct source_id from {W} w where w.in_scope
        and w.type in ({TYPES}) and w.publication_year between {LO} and {INCOMPLETE_YEAR}
        and w.source_type = 'journal' and w.source_id is not null and {CANDIDATE} order by 1""").fetchall()]
    evidence = journal_evidence(ids)
    con.execute("create table ev (source_id varchar, n int)")
    con.executemany("insert into ev values (?, ?)", list(evidence.items()))
    names = dict(con.execute(f"select source_id, any_value(source_name) from {W} group by 1").fetchall())
    write(DERIVED / "crosschecks" / "green_proxy_journals.csv",
          [{"source_id": s, "journal": names.get(s), "accepted_manuscript_repository_articles_2015_2025": n,
            "shows_deposit_evidence": n >= THRESHOLD} for s, n in sorted(evidence.items())])

    # Per institution and statewide, 2015-2025, works counted once per entity
    base = f"""from {W} w join {WI} wi using (work_id) left join ev using (source_id)
        where w.in_scope and wi.in_scope and w.type in ({TYPES})"""
    def agg(where_entity: str, key: str):
        r = con.execute(f"""select
            count(distinct w.work_id) filter (where w.oa_category='closed'),
            count(distinct w.work_id) filter (where w.oa_category='bronze'),
            count(distinct w.work_id) filter (where {CANDIDATE} and w.oa_category='closed' and ev.n >= {THRESHOLD}),
            count(distinct w.work_id) filter (where {CANDIDATE} and w.oa_category='bronze' and ev.n >= {THRESHOLD}),
            count(distinct w.work_id) filter (where {CANDIDATE} and ev.n >= 1),
            count(distinct w.work_id) filter (where {CANDIDATE} and ev.n >= 10),
            count(distinct w.work_id)
            {base} and w.publication_year between {LO} and {HI} {where_entity}""").fetchone()
        return {"entity": key, "articles": r[6], "closed": r[0], "bronze": r[1],
                "meeting_abstracts_excluded": con.execute(f"""select count(distinct w.work_id) {base}
                    and w.publication_year between {LO} and {HI} {where_entity}
                    and w.oa_category in ('closed','bronze') and {MEETING_ABSTRACT}""").fetchone()[0],
                "closed_candidates": r[2], "bronze_candidates": r[3],
                "candidates": r[2] + r[3], "candidates_share_of_articles": round((r[2] + r[3]) / r[6], 4),
                "candidates_if_threshold_1": r[4], "candidates_if_threshold_10": r[5]}
    rows = [agg("", "statewide"), agg("and wi.institution_key <> 'yale'", "statewide_without_yale")]
    rows += [agg(f"and wi.institution_key = '{k}'", k) for k, *_ in INSTITUTIONS]
    write(DERIVED / "metrics" / "green_opportunity_2015_2025.csv", rows)

    # Article list for librarians (all years incl. 2026); no author names
    cand = con.execute(f"""select wi.institution_key, w.work_id, w.doi, w.title, w.publication_year, w.source_name,
        w.publisher_parent_name, w.oa_category, ev.n
        {base} and w.publication_year between {LO} and {INCOMPLETE_YEAR} and {CANDIDATE} and ev.n >= {THRESHOLD}
        order by wi.institution_key, w.publication_year desc, w.source_name, w.work_id""").fetchall()
    write(DERIVED / "downloads" / "repository_candidates.csv",
          [{"institution": NAMES[c[0]], "institution_key": c[0], "openalex_id": c[1], "doi": c[2], "title": c[3],
            "year": c[4], "year_complete": c[4] <= HI, "journal": c[5], "publisher": c[6],
            "current_status": c[7], "journal_deposit_evidence_articles": c[8]} for c in cand])
    print(f"journals: {len(ids)}, with evidence >= {THRESHOLD}: {sum(n >= THRESHOLD for n in evidence.values())}")
    for r in rows[:3]:
        print(r)
    print("candidate rows (institution x article, 2015-2026):", len(cand))


if __name__ == "__main__":
    main()
