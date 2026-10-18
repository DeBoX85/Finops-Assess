"""Check registry and runner. A check that cannot run is reported as 'not_assessed' with a reason (hard rule 6)."""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class CheckMeta:
    id: str
    domain: str
    title: str
    collectors: tuple  # snapshot names this check needs
    permissions: tuple  # e.g. ("Reader",)
    billing_types: tuple = ("all",)
    run_cost: str = "low"  # low | medium | high
    confidence: str = "high"
    savings_basis: str = "none"  # none | actual | list | estimate
    framework: str = ""  # finops.org capability name
    validation: str = "offline-only"  # offline-only | live (live only after gate G2 passed on a real tenant)


@dataclass
class Finding:
    check_id: str
    resource_id: str
    severity: str
    message: str
    details: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)  # filled by the runner: logic hash, collectors, snapshot digests
    fingerprint: str = ""  # filled by the runner: sha256 over check, resource and details


class NotAssessed(Exception):
    """Raised by a check that cannot decide with the data it has; the runner reports 'not_assessed' with this reason (hard rule 6)."""


def collected_at(snapshot):
    """Reference time for age rules: when the snapshot was collected, never the wall clock, so offline re-analysis is reproducible."""
    import datetime as dt  # noqa: PLC0415

    m = snapshot.load("_meta") or {}
    raw = m.get("collected_at")
    if not raw:
        raise NotAssessed("snapshot has no collection time (_meta.json), so age rules cannot be applied")
    return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))


REGISTRY: list = []


def fingerprint(f) -> str:
    """Stable identity of a finding. Same inputs give the same value on every run."""
    raw = json.dumps([f.check_id, f.resource_id, f.details], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def logic_hash(fn) -> str:
    """Short hash of the check function source, so a report shows which rule version produced a finding."""
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return "unavailable"
    return hashlib.sha256(src.encode()).hexdigest()[:12]


def load_builtin():
    """Import built-in checks so they register. Explicit, so linters cannot remove the import."""
    from . import checks_builtin  # noqa: F401, PLC0415


def check(meta: CheckMeta):
    def deco(fn):
        REGISTRY.append((meta, fn))
        return fn

    return deco


def run_all(config, snapshot, registry=None):
    findings, status = [], []
    if registry is None:
        load_builtin()
    for meta, fn in registry if registry is not None else REGISTRY:
        ok, why = config.enabled(meta)
        if not ok:
            status.append({"id": meta.id, "status": "skipped", "reason": why})
            continue
        missing = [c for c in meta.collectors if not snapshot.has(c)]
        if missing:
            status.append({"id": meta.id, "status": "not_assessed", "reason": f"missing collector data: {', '.join(missing)}"})
            continue
        try:
            got = list(fn(snapshot))
        except NotAssessed as e:
            status.append({"id": meta.id, "status": "not_assessed", "reason": str(e)})
            continue
        except Exception as e:  # noqa: BLE001  one failing check must not stop the run; it is reported as failed
            status.append({"id": meta.id, "status": "failed", "reason": f"{type(e).__name__}: {e}"})
            continue
        lh = logic_hash(fn)
        for f in got:
            f.evidence = {
                "logic_hash": lh,
                "collectors": list(meta.collectors),
                "snapshot_digests": {c: snapshot.digest(c) for c in meta.collectors},
            }
            f.fingerprint = fingerprint(f)
        findings.extend(got)
        status.append({"id": meta.id, "status": "ran", "findings": len(got)})
    findings.sort(key=lambda f: (f.check_id, f.resource_id))  # stable order so reports are reproducible
    return findings, status


def meta_dict(meta):
    return asdict(meta)
