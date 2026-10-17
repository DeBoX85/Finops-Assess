from .checks import check, CheckMeta, Finding

@check(CheckMeta(id="ORPH-DISK-01", domain="orphaned", title="Unattached managed disks",
                 collectors=("unattached_disks",), permissions=("Reader",), savings_basis="none",
                 confidence="high", framework="Usage Optimization"))
def unattached_disks(snap):
    # Phase 1: no savings figure yet. Savings need cost data (actual) and list price; added in Phase 3.
    for d in snap.load("unattached_disks")["rows"]:
        yield Finding("ORPH-DISK-01", d["id"], "medium",
                      f"Unattached disk ({d.get('sizeGB')} GB, {d.get('skuName')}) incurs storage cost",
                      {k: d.get(k) for k in ("location", "skuName", "sizeGB", "timeCreated", "diskState")})
