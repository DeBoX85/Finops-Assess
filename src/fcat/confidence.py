"""Effective confidence label per check (backlog 46, docs/AUDIT.md section 4).

The label a check declares in code is a ceiling. "high" is shown only when measured precision (data/precision_records.toml) meets the owner's
thresholds (data/confidence_policy.toml); otherwise it is capped at "medium" and the note says why. Lower labels are never raised.
The note always states the sample, so a reader can judge it: a point estimate from 20 findings is weak evidence (17 of 20 correct is compatible
with a true rate of about 64 to 95 percent, 95 percent Wilson interval, own calculation)."""

from __future__ import annotations

import tomllib
from importlib import resources
from typing import Any

LABELS = ("low", "medium", "high")


def _load(name: str) -> dict:
    return tomllib.loads(resources.files("fcat").joinpath("data", name).read_text(encoding="utf-8"))


def _int(v, what: str) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise ValueError(f"{what} must be a non-negative whole number")
    return v


def load_policy(raw: dict | None = None) -> dict:
    p = (raw if raw is not None else _load("confidence_policy.toml")).get("policy")
    if not isinstance(p, dict):
        raise ValueError("confidence policy: missing [policy] table")
    prec = p.get("min_precision")
    if isinstance(prec, bool) or not isinstance(prec, (int, float)):
        raise ValueError("confidence policy: min_precision must be a number above 0 and at most 1")
    if not 0 < prec <= 1:
        raise ValueError("confidence policy: min_precision must be a number above 0 and at most 1")
    out: dict[str, Any] = {
        "min_precision": float(prec),
        "min_audited": _int(p.get("min_audited"), "min_audited"),
        "min_environments": _int(p.get("min_environments"), "min_environments"),
        "proposed_on": str(p.get("proposed_on") or ""),
        "confirmed_by_owner_on": str(p.get("confirmed_by_owner_on") or ""),
    }
    if out["min_audited"] < 1 or out["min_environments"] < 1:
        raise ValueError("confidence policy: min_audited and min_environments must be at least 1")
    return out


def load_records(raw: dict | None = None) -> dict:
    out: dict[str, Any] = {}
    for cid, r in (raw if raw is not None else _load("precision_records.toml")).items():
        if not isinstance(r, dict):
            raise ValueError(f"precision record {cid}: must be a table")
        rec: dict[str, Any] = {k: _int(r.get(k), f"precision record {cid}.{k}") for k in ("audited", "correct", "environments")}
        if rec["correct"] > rec["audited"]:
            raise ValueError(f"precision record {cid}: correct is larger than audited")
        rec["last_audit"] = str(r.get("last_audit") or "")
        out[cid] = rec
    return out


def effective(check_id: str, declared: str, policy: dict, records: dict) -> tuple[str, str]:
    """-> (label shown, plain-words note)."""
    rec = records.get(check_id)
    if rec is None or rec["audited"] == 0:
        measured = "precision not yet measured"
        sample = None
    else:
        pct = 100 * rec["correct"] / rec["audited"]
        sample = (
            f"{rec['correct']} of {rec['audited']} audited findings correct ({pct:.0f} percent) across {rec['environments']} environment(s)"
        )
        measured = sample
    if declared != "high":
        return declared, measured[0].upper() + measured[1:] + "."
    need = f"{policy['min_precision'] * 100:.0f} percent on at least {policy['min_audited']} audited findings across at least {policy['min_environments']} environments"
    if (
        rec is not None
        and rec["audited"] >= policy["min_audited"]
        and rec["environments"] >= policy["min_environments"]
        and rec["correct"] / rec["audited"] >= policy["min_precision"]
    ):
        return "high", f"{sample}; meets the rule ({need})."
    return "medium", f"Capped at medium: {measured}; 'high' needs {need}."


def policy_text(policy: dict) -> str:
    c = policy["confirmed_by_owner_on"]
    return (
        f"'High' confidence needs {policy['min_precision'] * 100:.0f} percent correct on at least {policy['min_audited']} audited findings "
        f"across at least {policy['min_environments']} environments. "
        + (
            f"Thresholds confirmed by the owner on {c}."
            if c
            else "Thresholds proposed on " + (policy["proposed_on"] or "?") + ", not yet confirmed by the owner."
        )
    )
