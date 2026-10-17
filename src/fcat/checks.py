"""Check registry and runner. A check that cannot run is reported as 'not_assessed' with a reason (hard rule 6)."""

from __future__ import annotations

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


REGISTRY: list = []


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
        except Exception as e:  # noqa: BLE001  one failing check must not stop the run; it is reported as failed
            status.append({"id": meta.id, "status": "failed", "reason": f"{type(e).__name__}: {e}"})
            continue
        findings.extend(got)
        status.append({"id": meta.id, "status": "ran", "findings": len(got)})
    return findings, status


def meta_dict(meta):
    return asdict(meta)
