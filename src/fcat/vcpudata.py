"""VM size to vCPU lookup for Windows VMs (opt-in `[run] compute_apis = true`), used by the Hybrid Benefit checks.

Why: Resource Graph does not return the vCPU count of a VM size. Learn (Azure Hybrid Benefit for Windows VMs, read 2026-10-27, https://learn.microsoft.com/azure/virtual-machines/windows/hybrid-use-benefit-licensing):
a minimum of 8 core licences per VM applies, so a 4-vCPU VM still uses 8; larger VMs need licences equal to their vCPU count.
Call: GET /subscriptions/{id}/providers/Microsoft.Compute/skus?$filter=location eq '{region}' (already allowed: GET on management.azure.com; same call and parser
as the opt-in rightsizing collector, src/fcat/metrics.py). One call per subscription and region that holds a Windows VM. Reader is expected to be enough
(UNVERIFIED live). Size names that the SKU list does not return are simply absent: the checks never guess a vCPU count."""

from __future__ import annotations

from . import metrics

MAX_PAIRS = 200


def _windows_vms(snapshot):
    for r in (snapshot.load("vm_licensing") or {}).get("rows", []):
        if (
            isinstance(r, dict)
            and str(r.get("osType") or "").lower() == "windows"
            and isinstance(r.get("subscriptionId"), str)
            and r["subscriptionId"]
            and isinstance(r.get("location"), str)
            and r["location"]
            and isinstance(r.get("vmSize"), str)
            and r["vmSize"]
        ):
            yield r


def collect_vm_vcpus(client, snapshot, config, errors: list):
    """Writes snapshot 'vm_vcpus': {'rows': [{subscriptionId, location, size, vcpus}], 'scopes': [{subscriptionId, location, status}], 'truncated', 'api_version'}.
    Only sizes used by Windows VMs are kept. Nothing is written when no SKU list could be read, so checks say 'not assessed' (lesson M-008)."""
    if not snapshot.has("vm_licensing"):
        errors.append(
            {"collector": "vm_vcpus", "error": "VM licensing inventory (vm_licensing) is missing, so no region could be selected"}
        )
        return
    wanted: dict = {}
    for r in _windows_vms(snapshot):
        wanted.setdefault((r["subscriptionId"], r["location"].lower()), set()).add(r["vmSize"])
    pairs = sorted(wanted)[:MAX_PAIRS]
    if not pairs:
        return
    rows, scopes = [], []
    for sub, loc in pairs:
        pages, err = metrics._get_pages(client, metrics.skus_url(sub, loc))
        if err:
            scopes.append({"subscriptionId": sub, "location": loc, "status": err})
            errors.append({"collector": "vm_vcpus", "error": f"SKU list for subscription {sub} region {loc}: {err}"})
            continue
        table = metrics.parse_skus(pages)
        scopes.append({"subscriptionId": sub, "location": loc, "status": "ok"})
        rows += [{"subscriptionId": sub, "location": loc, "size": s, "vcpus": table[s]} for s in sorted(wanted[(sub, loc)]) if s in table]
    if not any(s["status"] == "ok" for s in scopes):
        return
    snapshot.save("vm_vcpus", {"rows": rows, "scopes": scopes, "truncated": len(wanted) > len(pairs), "api_version": metrics.SKUS_API})
