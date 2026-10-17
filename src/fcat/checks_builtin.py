from .checks import CheckMeta, Finding, check

# ADR 0004 (hybrid): KQL narrows to unmanaged-by-VM disks; the rules below live in Python so they are unit tested.
# Mirrors the finops-toolkit ORPH logic (MIT): skip disks in ActiveSAS state and ASR replica/seed disks.
EXCLUDED_STATES = {"ActiveSAS"}
EXCLUDED_TAG_KEYS = {"asr-replicadisk", "asrseeddisk"}


def _excluded(d) -> str | None:
    if d.get("diskState") in EXCLUDED_STATES:
        return f"diskState {d.get('diskState')}"
    tags = d.get("tags") or {}
    if isinstance(tags, dict) and EXCLUDED_TAG_KEYS & {str(k).lower() for k in tags}:
        return "ASR replica/seed tag"
    return None


@check(
    CheckMeta(
        id="ORPH-DISK-01",
        domain="orphaned",
        title="Unattached managed disks",
        collectors=("unattached_disks",),
        permissions=("Reader",),
        savings_basis="none",
        confidence="high",
        framework="Usage Optimization",
    )
)
def unattached_disks(snap):
    # Phase 1: no savings figure yet. Savings need cost data (actual) and list price; added in Phase 3.
    for d in snap.load("unattached_disks")["rows"]:
        if _excluded(d):
            continue
        yield Finding(
            "ORPH-DISK-01",
            d["id"],
            "medium",
            f"Unattached disk ({d.get('sizeGB')} GB, {d.get('skuName')}) incurs storage cost",
            {k: d.get(k) for k in ("location", "skuName", "sizeGB", "timeCreated", "diskState")},
        )
