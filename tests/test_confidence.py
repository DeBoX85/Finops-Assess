"""Effective confidence (src/fcat/confidence.py, backlog 46): 'high' only when measured precision meets the owner's thresholds."""

import pytest

from fcat import checks, confidence

POL = {"min_precision": 0.85, "min_audited": 20, "min_environments": 2, "proposed_on": "2026-10-27", "confirmed_by_owner_on": ""}


def rec(audited, correct, env=2):
    return {"X-Y-01": {"audited": audited, "correct": correct, "environments": env, "last_audit": ""}}


def test_unmeasured_high_is_capped_to_medium_and_says_so():
    label, note = confidence.effective("X-Y-01", "high", POL, {})
    assert label == "medium" and "precision not yet measured" in note and "85 percent" in note and "20 audited" in note


def test_high_needs_all_three_limits_exactly():
    assert (
        confidence.effective("X-Y-01", "high", POL, rec(20, 17))[0] == "high"
    )  # 85 percent on 20 across 2 environments: on the line, allowed
    assert confidence.effective("X-Y-01", "high", POL, rec(20, 16))[0] == "medium"  # 80 percent
    assert confidence.effective("X-Y-01", "high", POL, rec(19, 19))[0] == "medium"  # sample too small
    assert confidence.effective("X-Y-01", "high", POL, rec(30, 30, env=1))[0] == "medium"  # one environment only
    label, note = confidence.effective("X-Y-01", "high", POL, rec(20, 17))
    assert "17 of 20" in note and "85 percent" in note


def test_failing_note_shows_the_sample():
    _, note = confidence.effective("X-Y-01", "high", POL, rec(20, 12))
    assert "12 of 20" in note and "60 percent" in note and "Capped at medium" in note


def test_measurement_never_raises_a_lower_label():
    for declared in ("low", "medium"):
        assert confidence.effective("X-Y-01", declared, POL, rec(100, 100))[0] == declared


def test_zero_audited_counts_as_unmeasured():
    assert "not yet measured" in confidence.effective("X-Y-01", "high", POL, rec(0, 0))[1]


def test_policy_validation():
    base = {"policy": {"min_precision": 0.85, "min_audited": 20, "min_environments": 2}}
    assert confidence.load_policy(base)["min_audited"] == 20
    for bad in (
        {"min_precision": 0},
        {"min_precision": 1.5},
        {"min_precision": True},
        {"min_audited": 0},
        {"min_audited": 2.5},
        {"min_environments": -1},
    ):
        with pytest.raises(ValueError):
            confidence.load_policy({"policy": {**base["policy"], **bad}})
    with pytest.raises(ValueError):
        confidence.load_policy({})


def test_record_validation():
    assert confidence.load_records({"A-B-01": {"audited": 5, "correct": 4, "environments": 1}})["A-B-01"]["correct"] == 4
    for bad in (
        {"audited": 5, "correct": 6, "environments": 1},
        {"audited": "5", "correct": 4, "environments": 1},
        {"audited": 5, "correct": 4},
    ):
        with pytest.raises(ValueError):
            confidence.load_records({"A-B-01": bad})
    with pytest.raises(ValueError):
        confidence.load_records({"A-B-01": 3})


def test_policy_text_states_whether_the_owner_confirmed():
    assert "not yet confirmed by the owner" in confidence.policy_text(POL)
    assert "confirmed by the owner on 2026-11-01" in confidence.policy_text({**POL, "confirmed_by_owner_on": "2026-11-01"})


def test_shipped_files_load_and_every_record_matches_a_real_check():
    p, r = confidence.load_policy(), confidence.load_records()
    assert p["min_precision"] == 0.85 and p["min_audited"] == 20 and p["min_environments"] == 2
    checks.load_builtin()
    assert set(r) <= {m.id for m, _ in checks.REGISTRY}


def test_catalogue_shows_effective_and_declared_label():
    checks.load_builtin()
    meta = next(m for m, _ in checks.REGISTRY if m.confidence == "high")
    d = checks.meta_dict(meta, POL, {})
    assert d["confidence"] == "medium" and d["confidence_declared"] == "high" and "not yet measured" in d["confidence_note"]
