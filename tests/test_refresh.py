"""The monthly refresh must stop on a broken harvest and pass ordinary change."""
import pandas as pd

from pipeline.refresh_report import checks


def table(state_works, state_share, a_works=1000, a_share=0.5):
    return pd.DataFrame([
        ("statewide", "CT", state_works, state_share),
        ("statewide_no_yale", "CT no Yale", 500, 0.5),
        ("a", "Inst A", a_works, a_share),
        ("b", "Inst B", 300, 0.4),
    ], columns=["entity", "entity_name", "works", "free_to_read_share"])


COMPLETE = pd.DataFrame({"group_by_count": [100, 50], "diff": [0, 0]})
OLD = table(10000, 0.67)


def failed(results):
    return [name for name, ok, _ in results if not ok]


def test_ordinary_month_passes():
    assert failed(checks(OLD, table(10150, 0.675, 1010, 0.51), COMPLETE)) == []


def test_short_harvest_fails():
    gap = pd.DataFrame({"group_by_count": [100, 50], "diff": [-3, 0]})  # 3% of one cell missing
    assert any("Harvest" in f for f in failed(checks(OLD, OLD, gap)))


def test_lost_articles_fail():
    assert any("Statewide articles" in f for f in failed(checks(OLD, table(9500, 0.67), COMPLETE)))
    assert any("loses" in f for f in failed(checks(OLD, table(10000, 0.67, a_works=850), COMPLETE)))


def test_big_share_jump_fails():
    assert any("Statewide share" in f for f in failed(checks(OLD, table(10000, 0.71), COMPLETE)))
    assert any("8 points" in f for f in failed(checks(OLD, table(10000, 0.67, a_share=0.6), COMPLETE)))
