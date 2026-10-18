"""Peak-aware CPU rightsizing statistics (docs/RIGHTSIZING.md, DEV-PRINCIPLES R10). Pure functions: no I/O, no clock.
Thresholds are policy parameters (PROPOSAL, not Microsoft's numbers) and are echoed in every result so a reader can see what was applied."""

from __future__ import annotations

from dataclasses import asdict, dataclass

MIN_WINDOW_DAYS = 14
MIN_COVERAGE = 0.90
MEDIUM_WINDOW_DAYS = 30


@dataclass(frozen=True)
class Point:
    hour_index: int  # hours since window start; used only to count distinct hours
    cpu_max: float  # maximum CPU % seen in that hour
    cpu_avg: float  # average CPU % in that hour


def percentile(values, q: float) -> float:
    """Nearest-rank percentile (q in 0..100) on a copy; deterministic, no interpolation, so peaks are not smoothed away."""
    if not values:
        raise ValueError("no values")
    s = sorted(values)
    rank = max(1, -(-int(q * len(s)) // 100)) if q < 100 else len(s)  # ceil(q/100*n) via integers
    return s[min(rank, len(s)) - 1]


def assess_cpu(
    points, expected_hours: int, current_vcpus: int, target_vcpus: int, *, limit_pct: float = 60.0, credits_exhausted: bool = False
) -> dict:
    """expected_hours = hours the VM was running in the window (deallocated hours emit no metrics and must not count against coverage)."""
    if not (isinstance(current_vcpus, int) and isinstance(target_vcpus, int)) or current_vcpus <= 0 or target_vcpus <= 0:
        raise ValueError("vCPU counts must be positive integers")
    if target_vcpus >= current_vcpus:
        raise ValueError("target must be smaller than current; this assesses downsizing only")
    pts = {p.hour_index: p for p in points}  # duplicates for one hour collapse to the last seen
    n = len(pts)
    coverage = (n / expected_hours) if expected_hours > 0 else 0.0
    window_days = expected_hours / 24
    params = {
        "limit_pct": limit_pct,
        "min_window_days": MIN_WINDOW_DAYS,
        "min_coverage": MIN_COVERAGE,
        "scale": current_vcpus / target_vcpus,
    }
    base = {"window_days": round(window_days, 1), "points": n, "coverage": round(coverage, 3), "parameters": params}
    if n == 0 or window_days < MIN_WINDOW_DAYS or coverage < MIN_COVERAGE:
        return {
            **base,
            "verdict": "insufficient_data",
            "confidence": "low",
            "reason": "window shorter than 14 days, coverage below 90%, or no data",
        }
    maxes = [p.cpu_max for p in pts.values()]
    avgs = [p.cpu_avg for p in pts.values()]
    scale = current_vcpus / target_vcpus
    stats = {"p99_hourly_max": percentile(maxes, 99), "max_hourly_max": max(maxes), "p95_hourly_avg": percentile(avgs, 95)}
    projected = stats["p99_hourly_max"] * scale
    stats["projected_p99_hourly_max"] = round(projected, 2)
    if credits_exhausted:
        return {
            **base,
            **stats,
            "verdict": "keep",
            "confidence": "low",
            "reason": "burstable VM exhausted its CPU credits in the window; it is already starved",
        }
    verdict = "candidate" if projected <= limit_pct else "keep"
    conf = "medium" if window_days >= MEDIUM_WINDOW_DAYS else "low"  # never 'high' before live validation
    return {
        **base,
        **stats,
        "verdict": verdict,
        "confidence": conf,
        "reason": f"projected P99 of hourly maximum {projected:.1f}% vs limit {limit_pct}%",
    }


def as_dict(p: Point) -> dict:
    return asdict(p)
