import random

import pytest

from fcat.rightsize import Point, assess_cpu, percentile

H30 = 30 * 24


def series(hours, base_max=20.0, base_avg=8.0, spike=None):
    pts = []
    for h in range(hours):
        mx = base_max
        if spike and h % 24 == 2:
            mx = spike  # nightly job
        pts.append(Point(h, mx, base_avg))
    return pts


def test_steady_low_load_is_candidate_with_medium_confidence():
    r = assess_cpu(series(H30), H30, 8, 4)
    assert r["verdict"] == "candidate" and r["confidence"] == "medium" and r["projected_p99_hourly_max"] == 40.0


def test_low_average_with_short_spike_is_kept():
    """The R10 case: the average is 8% but the nightly job peaks at 95%."""
    r = assess_cpu(series(H30, spike=95.0), H30, 8, 4)
    assert r["verdict"] == "keep" and r["p95_hourly_avg"] == 8.0 and r["max_hourly_max"] == 95.0


def test_short_window_or_low_coverage_is_insufficient_not_candidate():
    assert assess_cpu(series(7 * 24), 7 * 24, 8, 4)["verdict"] == "insufficient_data"
    sparse = series(H30)[::2]  # half the hours missing
    assert assess_cpu(sparse, H30, 8, 4)["verdict"] == "insufficient_data"
    assert assess_cpu([], H30, 8, 4)["verdict"] == "insufficient_data"
    assert assess_cpu(series(H30), 0, 8, 4)["verdict"] == "insufficient_data"


def test_14_to_29_day_window_caps_confidence_at_low():
    r = assess_cpu(series(14 * 24), 14 * 24, 8, 4)
    assert r["verdict"] == "candidate" and r["confidence"] == "low"


def test_confidence_is_never_high():
    assert all(assess_cpu(series(h), h, 16, 4)["confidence"] != "high" for h in (14 * 24, 30 * 24, 90 * 24))


def test_exhausted_credits_never_candidate():
    assert assess_cpu(series(H30), H30, 8, 4, credits_exhausted=True)["verdict"] == "keep"


def test_halving_vcpus_doubles_projected_peak():
    # derived by hand: 35% * (8/4) = 70% > 60% limit -> keep; 25% * 2 = 50% <= 60% -> candidate
    assert assess_cpu(series(H30, base_max=35.0), H30, 8, 4)["verdict"] == "keep"
    assert assess_cpu(series(H30, base_max=25.0), H30, 8, 4)["verdict"] == "candidate"
    assert assess_cpu(series(H30, base_max=25.0), H30, 8, 2)["verdict"] == "keep"  # 25 * 4 = 100


@pytest.mark.parametrize("bad", [(0, 1), (4, 0), (4, 4), (2, 4), (4.0, 2)])
def test_bad_vcpu_inputs_are_rejected(bad):
    with pytest.raises(ValueError):
        assess_cpu(series(H30), H30, *bad)


def test_percentile_is_nearest_rank_and_never_below_the_data():
    v = list(range(1, 101))
    assert percentile(v, 99) == 99 and percentile(v, 100) == 100 and percentile(v, 50) == 50
    assert percentile([7], 99) == 7
    with pytest.raises(ValueError):
        percentile([], 50)


def test_order_and_duplicate_hours_do_not_change_the_verdict():
    rnd = random.Random(1)
    pts = series(H30, spike=50.0)
    ref = assess_cpu(pts, H30, 8, 4)
    shuffled = pts[:]
    rnd.shuffle(shuffled)
    assert assess_cpu(shuffled, H30, 8, 4) == ref
    assert assess_cpu(pts + pts[:100], H30, 8, 4) == ref  # same hours repeated collapse


def test_metamorphic_raising_any_peak_never_turns_keep_into_candidate():
    rnd = random.Random(2)
    for _ in range(50):
        mx = [rnd.uniform(1, 90) for _ in range(H30)]
        pts = [Point(i, m, m / 2) for i, m in enumerate(mx)]
        before = assess_cpu(pts, H30, 8, 4)["verdict"]
        i = rnd.randrange(H30)
        pts[i] = Point(i, min(100.0, mx[i] + 30), mx[i] / 2)
        after = assess_cpu(pts, H30, 8, 4)["verdict"]
        assert not (before == "keep" and after == "candidate")
