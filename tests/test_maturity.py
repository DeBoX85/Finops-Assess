import json
import pathlib
import re

import pytest

from fcat import cli, maturity

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_twenty_two_capabilities():
    assert len(maturity.CAPABILITIES) == 22 and len(set(maturity.CAPABILITIES)) == 22


def test_question_map_matches_the_design_doc():
    text = (ROOT / "docs" / "maturity" / "README.md").read_text()
    line = next(x for x in text.splitlines() if x.startswith("Q1 "))
    parts = re.split(r"(?<=\.) (?=Q\d+ )", line)
    assert len(parts) == len(maturity.QMAP)
    for part in parts:
        q = int(re.match(r"Q(\d+) ", part).group(1))
        body = part[len(f"Q{q} ") :].rstrip(".").replace(" (partial)", "")
        for cap in sorted(maturity.QMAP[q], key=len, reverse=True):
            assert cap in body, (q, cap)
            body = body.replace(cap, "", 1)
        assert re.fullmatch(r"[\s,]*(and)?[\s,]*", body.replace(" and ", " ")) or body.strip(" ,and") == "", (q, body)


def _ev(answers, targets=None):
    return maturity.evaluate({"answers": answers, "targets": targets or {}})


def _row(res, cap):
    return next(r for r in res["capabilities"] if r["capability"] == cap)


def test_levels_and_target_status():
    res = _ev({"q4": "B"}, {"Budgeting": "run", "forecasting": "walk"})
    assert _row(res, "Budgeting")["status"] == "below" and _row(res, "Budgeting")["current"] == "walk"
    assert _row(res, "Forecasting")["status"] == "meets"  # case-insensitive target name


def test_above_and_no_target():
    res = _ev({"q6": "C"}, {"Anomaly Management": "walk"})
    assert _row(res, "Anomaly Management")["status"] == "above"
    assert _row(_ev({"q6": "C"}), "Anomaly Management")["status"] == "no_target"


def test_not_sure_is_needs_input_never_zero():
    res = _ev({"q6": "D"}, {"Anomaly Management": "walk"})
    r = _row(res, "Anomaly Management")
    assert r["status"] == "needs_input" and r["current"] is None and r["unsure_questions"] == [6]


def test_shared_capability_takes_lowest_answer_and_flags_partial():
    res = _ev({"q1": "C", "q2": "A"})  # Executive Strategy Alignment is mapped to q1 and q2
    assert _row(res, "Executive Strategy Alignment")["current"] == "crawl"
    res = _ev({"q8": "C", "q12": "D"})  # Sustainability mapped to q8 and q12
    r = _row(res, "Sustainability")
    assert r["current"] == "run" and r["partial"] is True


def test_no_default_target_is_invented():
    assert all(r["target"] is None for r in _ev({"q1": "A"})["capabilities"])


@pytest.mark.parametrize(
    "bad",
    [
        {"answers": {"q14": "A"}},
        {"answers": {"q1": "E"}},
        {"answers": {"x": "A"}},
        {"targets": {"Nope": "walk"}},
        {"targets": {"Budgeting": "expert"}},
    ],
)
def test_bad_input_is_rejected(bad):
    with pytest.raises(maturity.MaturityError):
        maturity.evaluate(bad)


def test_unknown_table_rejected(tmp_path):
    p = tmp_path / "m.toml"
    p.write_text("[surprise]\nx=1\n")
    with pytest.raises(maturity.MaturityError):
        maturity.load(p)


def test_cli_writes_outputs(tmp_path, capsys):
    p = tmp_path / "m.toml"
    p.write_text('[answers]\nq4 = "B"\nq6 = "D"\n[targets]\nBudgeting = "run"\n')
    assert cli.main(["maturity", str(p), "--out", str(tmp_path / "o"), "--allow-unignored-out"]) == 0
    res = json.loads((tmp_path / "o" / "maturity.json").read_text())
    assert res["counts"]["below"] == 1
    md = (tmp_path / "o" / "maturity.md").read_text()
    assert "answers only" in md and "Budgeting" in md
    assert "below target 1" in capsys.readouterr().out


def test_cli_bad_input_exit_2(tmp_path, capsys):
    p = tmp_path / "m.toml"
    p.write_text('[answers]\nq1 = "Z"\n')
    assert cli.main(["maturity", str(p), "--out", str(tmp_path / "o"), "--allow-unignored-out"]) == 2


def test_every_capability_has_exactly_one_domain():
    assert set(maturity.DOMAIN_OF) == set(maturity.CAPABILITIES) and len(maturity.DOMAINS) == 4
    assert sum(len(v) for v in maturity.DOMAINS.values()) == 22
    assert all(r["domain"] in maturity.DOMAINS for r in _ev({})["capabilities"])
