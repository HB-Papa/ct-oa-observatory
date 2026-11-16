"""Known-answer tests for the phase 6 helpers (DOAJ classification, email
scrubbing, OpenAPC ratios, green proxy filter)."""
from pipeline import s10_doaj, s11_openapc, s12_green_proxy, sources


def test_doaj_classify():
    no_fee = {"in_doaj": True, "doaj_has_apc": False, "doaj_has_other_charges": False, "doaj_oa_start": 2010}
    fee = {"in_doaj": True, "doaj_has_apc": True, "doaj_oa_start": None}
    assert s10_doaj.classify(2020, None) == "not_in_doaj"
    assert s10_doaj.classify(2020, {"in_doaj": False}) == "not_in_doaj"
    assert s10_doaj.classify(2020, no_fee) == "doaj_no_fee"
    # published before the journal became open access: DOAJ says nothing about it
    assert s10_doaj.classify(2009, no_fee) == "published_before_doaj_oa_start"
    assert s10_doaj.classify(2020, no_fee | {"doaj_has_other_charges": True}) == "doaj_no_apc_but_other_charges"
    assert s10_doaj.classify(2015, fee) == "doaj_charges_fee"


def test_scrub_removes_email(monkeypatch):
    monkeypatch.setattr(sources, "SECRETS", ["someone@example.org"])
    url = "https://api.unpaywall.org/v2/10.1/x?email=someone%40example.org"
    assert "example.org" not in sources.scrub(url)
    assert sources.scrub("a someone@example.org b") == "a EMAIL_REMOVED b"


def test_openapc_summarise():
    # paid 50 of list 100, and 150 of list 100: totals 200/200 = 1.0, ratios 0.5 and 1.5, median 1.0
    s = s11_openapc.summarise("x", [(50, 100), (150, 100)])
    assert s["paid_as_share_of_list"] == 1.0 and s["median_article_ratio"] == 1.0 and s["articles"] == 2
    assert s11_openapc.summarise("empty", [])["articles"] == 0


def test_green_proxy_filter_excludes_funder_repositories():
    f = s12_green_proxy.evidence_filter(["S1", "S2"])
    assert "primary_location.source.id:S1|S2" in f
    assert "oa_status:green" in f and "best_oa_location.version:acceptedVersion" in f
    for r in s12_green_proxy.FUNDER_REPOSITORIES:
        assert f"best_oa_location.source.id:!{r}" in f
