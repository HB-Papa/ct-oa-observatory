"""Known-answer tests for turning one OpenAlex work into table rows."""
from pipeline.s04_build_tables import flatten

OA = "https://openalex.org/"


def inst(iid, lineage=None):
    return {"id": OA + iid, "lineage": [OA + x for x in (lineage or [iid])]}


def work(**over):
    w = {
        "id": OA + "W1", "doi": "https://doi.org/10.1/x", "title": "T", "publication_year": 2020,
        "publication_date": "2020-01-01", "type": "article", "language": "en",
        "open_access": {"is_oa": False, "oa_status": "closed", "any_repository_has_fulltext": False},
        "primary_location": {"id": "doi:1", "version": "publishedVersion",
                             "source": {"id": OA + "S1", "type": "journal",
                                        "host_organization_name": "Imprint",
                                        "host_organization_lineage_names": ["Imprint", "Parent Co"]}},
        "locations": [], "apc_list": {"value_usd": 3000}, "apc_paid": None,
        "corresponding_institution_ids": [], "authorships": [], "primary_topic": None,
    }
    w.update(over)
    return w


def test_uconn_health_rolls_up_to_uconn_and_counts_once():
    # Two authors: one at UConn, one at UConn Health. Both map to "uconn", one row.
    w = work(authorships=[{"institutions": [inst("I140172145")]},
                          {"institutions": [inst("I75929689")]}])
    _, wi, _ = flatten(w, "2026-11-15")
    assert [r["institution_key"] for r in wi] == ["uconn"]


def test_sub_unit_maps_through_lineage():
    # Yale Peabody Museum's lineage includes Yale, so the work counts for Yale.
    w = work(authorships=[{"institutions": [inst("I4387153325", ["I32971472", "I4387153325"])]}])
    work_row, wi, _ = flatten(w, "s")
    assert [r["institution_key"] for r in wi] == ["yale"]
    assert work_row["n_reported_institutions"] == 1


def test_out_of_scope_affiliation_is_ignored():
    w = work(authorships=[{"institutions": [inst("I1323778983")]},   # Yale New Haven Hospital
                          {"institutions": [inst("I100538780")]}])   # Wesleyan
    _, wi, _ = flatten(w, "s")
    assert [r["institution_key"] for r in wi] == ["wesleyan"]


def test_corresponding_institution_flag():
    w = work(authorships=[{"institutions": [inst("I32971472")]}, {"institutions": [inst("I100538780")]}],
             corresponding_institution_ids=[OA + "I100538780"])
    work_row, wi, _ = flatten(w, "s")
    flags = {r["institution_key"]: r["is_corresponding_institution"] for r in wi}
    assert flags == {"yale": False, "wesleyan": True}
    assert work_row["n_corresponding_institutions"] == 1


def test_publisher_parent_is_top_of_lineage():
    work_row, _, _ = flatten(work(), "s")
    assert work_row["publisher_name"] == "Imprint"
    assert work_row["publisher_parent_name"] == "Parent Co"


def test_repository_copy_flags():
    locs = [{"id": "a", "version": "acceptedVersion", "is_oa": True, "source": {"type": "repository"}},
            {"id": "b", "version": "submittedVersion", "is_oa": True, "source": {"type": "repository"}}]
    work_row, _, loc_rows = flatten(work(locations=locs), "s")
    assert work_row["has_repository_location"] is True
    assert work_row["has_oa_accepted_repository_copy"] is True
    assert work_row["has_oa_published_repository_copy"] is False
    assert len(loc_rows) == 2


def test_rule_a_excludes_repository_record_without_doi():
    repo_primary = {"id": "r", "version": "submittedVersion", "source": {"id": OA + "S9", "type": "repository"}}
    w = work(doi=None, primary_location=repo_primary,
             authorships=[{"institutions": [inst("I4498119")]}])
    work_row, wi, _ = flatten(w, "s")
    assert work_row["exclude_reason"] == "repository_record_no_doi"
    assert work_row["in_scope"] is False and wi[0]["in_scope"] is False


def test_rule_a_keeps_repository_record_with_doi_and_journal_without_doi():
    repo_primary = {"id": "r", "source": {"id": OA + "S9", "type": "repository"}}
    assert flatten(work(primary_location=repo_primary), "s")[0]["in_scope"] is True
    assert flatten(work(doi=None), "s")[0]["in_scope"] is True  # journal article, no DOI


def test_meeting_abstracts_excluded_by_doi_pattern():
    from pipeline.s04_build_tables import is_meeting_abstract
    for d in ["https://doi.org/10.1212/wnl.86.16_supplement.p5.123",
              "https://doi.org/10.1096/fasebj.2018.32.1_supplement.796.15",
              "https://doi.org/10.1200/jco.2025.43.5_suppl.559",
              "https://doi.org/10.1161/circ.150.suppl_1.4136704",
              "https://doi.org/10.1182/blood-2022-169754",
              "https://doi.org/10.1182/blood.v126.23.87.87"]:
        assert is_meeting_abstract(d), d
    for d in ["https://doi.org/10.1182/blood-2016-09-692954",       # regular Blood article
              "https://doi.org/10.5670/oceanog.2021.supplement.02-31",  # real article in a supplement issue
              "https://doi.org/10.18001/trs.3.2(suppl1).6", None]:
        assert not is_meeting_abstract(d), d
    row, wi, _ = flatten(work(doi="https://doi.org/10.1200/jco.2019.37.15_suppl.e123",
                              authorships=[{"institutions": [inst("I4498119")]}]), "s")
    assert row["exclude_reason"] == "meeting_abstract" and row["in_scope"] is False and wi[0]["in_scope"] is False


def test_trinity_washington_college_credit_is_corrected():
    # Author at Washington College (Maryland) matched by OpenAlex to Trinity.
    a = {"institutions": [inst("I56722557")], "raw_affiliation_strings": ["Washington College, USA"]}
    work_row, wi, _ = flatten(work(authorships=[a]), "s")
    assert wi[0]["affiliation_corrected"] is True and wi[0]["in_scope"] is False
    assert work_row["in_scope"] is False
    assert work_row["exclude_reason"] == "affiliation_correction_no_ct_institution"


def test_trinity_correction_keeps_real_trinity_and_other_institutions():
    wash = {"institutions": [inst("I56722557")], "raw_affiliation_strings": ["Washington College, USA"]}
    real = {"institutions": [inst("I56722557")], "raw_affiliation_strings": ["Trinity College, Hartford, CT"]}
    wes = {"institutions": [inst("I100538780")], "raw_affiliation_strings": ["Wesleyan University"]}
    _, wi, _ = flatten(work(authorships=[wash, real]), "s")
    assert wi[0]["in_scope"] is True                      # a real Trinity author is present
    row, wi2, _ = flatten(work(authorships=[wash, wes]), "s")
    flags = {r["institution_key"]: r["in_scope"] for r in wi2}
    assert flags == {"trinity": False, "wesleyan": True} and row["in_scope"] is True


def test_diamond_split():
    from pipeline.s04_build_tables import oa_category
    assert oa_category("diamond", 0) == "diamond"
    assert oa_category("diamond", 0.0) == "diamond"
    assert oa_category("diamond", None) == "oa_fee_unconfirmed"
    assert oa_category("diamond", 1500) == "oa_fee_unconfirmed"
    assert oa_category("gold", 0) == "gold" and oa_category("closed", None) == "closed"


def test_fairfield_institute_and_new_jersey_credits_are_corrected():
    from pipeline.s04_build_tables import corrected_out
    assert corrected_out("fairfield", ["Fairfield Institute of Management and Technology"])
    assert corrected_out("fairfield", ["MD1 Program, Fairfield, NJ"])
    # Fairfield University itself, with or without the state, is kept
    assert not corrected_out("fairfield", ["Fairfield University, Fairfield, CT 06824, USA"])
    assert not corrected_out("fairfield", ["Fairfield University"])
    assert not corrected_out("fairfield", ["Fairfield Institute of Management", "Fairfield University"])


def _credit(rows):
    return {r["institution_key"]: r for r in rows}


def test_yale_misattributions_removed_and_real_yale_kept():
    for text in ["The Collegiate School, NY 10024", "Department of Chemistry, Center for Light Energy Activated Redox "
                 "Processes (LEAP), Northwestern University", "Chan Zuckerberg Biohub New York | Columbia University",
                 "Assistant Professor, Yale-NUS College"]:
        _, wi, _ = flatten(work(authorships=[{"institutions": [inst("I32971472")], "raw_affiliation_strings": [text]}]), "s")
        assert _credit(wi)["yale"]["in_scope"] is False, text
    # Yale authors who also list a partner are kept
    _, wi, _ = flatten(work(authorships=[{"institutions": [inst("I32971472")],
                                          "raw_affiliation_strings": ["Yale University | Chan Zuckerberg Biohub New York"]}]), "s")
    assert _credit(wi)["yale"]["in_scope"] is True


def test_netter_school_of_medicine_moves_from_yale_to_quinnipiac():
    a = {"institutions": [inst("I32971472")], "raw_affiliation_strings": ["Frank H. Netter MD School of Medicine, North Haven, CT"]}
    w = work(authorships=[a], corresponding_institution_ids=[OA + "I32971472"])
    row, wi, _ = flatten(w, "s")
    c = _credit(wi)
    assert c["yale"]["in_scope"] is False and c["yale"]["affiliation_corrected"] is True
    assert c["quinnipiac"]["in_scope"] is True and c["quinnipiac"]["reassigned"] is True
    assert c["quinnipiac"]["is_corresponding_institution"] is True  # corresponding status moves with the credit
    assert row["in_scope"] is True


def test_saint_joseph_beirut_removed_and_west_hartford_kept():
    _, wi, _ = flatten(work(authorships=[{"institutions": [inst("I192633058")], "raw_affiliation_strings": ["Universite Saint-Joseph"]}]), "s")
    assert _credit(wi)["usj"]["in_scope"] is False
    _, wi, _ = flatten(work(authorships=[{"institutions": [inst("I192633058")],
                                          "raw_affiliation_strings": ["Saint Joseph University, West Hartford, CT"]}]), "s")
    assert _credit(wi)["usj"]["in_scope"] is True


def test_trinity_cambridge_removed_and_hartford_kept():
    from pipeline.s04_build_tables import corrected_out
    assert corrected_out("trinity", ["USC Dornsife INET, University of Southern California and Trinity College"])
    assert not corrected_out("trinity", ["Trinity College, Hartford, CT", "University of Cambridge"])


def test_manual_corrections_file_is_applied():
    from pipeline.s04_build_tables import MANUAL_CORRECTIONS, correction
    assert ("W3122090893", "uconn") in MANUAL_CORRECTIONS
    assert correction("uconn", ["anything"], "W3122090893") == (True, None)
    assert correction("uconn", ["anything"], "W0000000000") == (False, None)
