"""Tag discovery and hygiene logic (pure functions, no I/O). See docs/COST-GOVERNANCE.md and docs/KB/notes/11-cost-governance-azure.md.

Principle (owner, 2026-10-20): the tag standard comes from the customer's environment, never from a list in this tool.
Order of evidence: (1) tag names declared in the customer's own tag policies, (2) keys most resources already carry (inferred),
(3) none: say so. All thresholds below are OUR proposals, echoed in every finding that uses them.

Learn facts used (read 2026-10-20, tag-resources page): tag names are case-insensitive for operations but the casing is kept
and shows in cost reports; tag values are case-sensitive and appear as separate rows in cost reports. Whether Cost Management
merges name casings is UNVERIFIED, so wording is "may split reporting"."""

from __future__ import annotations

import re
from collections import Counter

SCHEME_SHARE_PCT = 50  # a key is "in the inferred scheme" when at least this share of resources carries it (our proposal)
GAP_PCT = 25  # TAG-COV-01 fires when at least this share of a subscription's resources lacks a scheme key (our proposal)
MIN_RESOURCES = 10  # ignore subscriptions with fewer resources, so tiny samples do not produce findings
RG_MIN_RESOURCES = 3
RG_GAP_PCT = 50

# Built-in tag policy definitions listed on Learn "Assign policy definitions for tag compliance" (read 2026-10-20).
# kind: require (deny), modify (add or add-or-replace), inherit (from resource group or subscription), append.
# The parameter name 'tagName' is VERIFIED only for 871b6d14 (RequireTag_Deny.json); for the others it is UNVERIFIED, so a missing
# parameter means "tag name not readable", never a guess.
TAG_DEFINITIONS = {
    "871b6d14-10aa-478d-b590-94f262ecfa99": "require",
    "1e30110a-5ceb-460c-a204-c1c3969c6d62": "require",
    "96670d01-0a4d-4649-9c89-2d3abc0a5025": "require",
    "8ce3da23-7156-49e4-b145-24f95f9dcb46": "require",
    "726aca4c-86e9-4b04-b0c5-073027359532": "modify",
    "4f9dc7db-30c1-420c-b61a-e1d640128d26": "modify",
    "96d9a89c-0d67-41fc-899d-2b9599f76a24": "modify",
    "d157c373-a6c4-483d-aaad-570756956268": "modify",
    "5ffd78d9-436d-4b41-a421-5baa819e3008": "modify",
    "61a4d60b-7326-440e-8051-9f94394d4dd1": "modify",
    "cd3aa116-8754-49c9-a813-ad46512ece54": "inherit",
    "ea3f2387-9b95-492a-a190-fcdc54f7b070": "inherit",
    "b27a0cbd-a167-4dfa-ae64-4337be671140": "inherit",
    "40df99da-1232-49b1-a39a-6da8d878f469": "inherit",
    "9ea02ca2-71db-412d-8b00-7c7ca9fcd32d": "append",
    "49c88fc8-6fd1-46fd-a676-f12d1d3a4c71": "append",
    "2a0e14a6-b0a6-4fab-991a-187a4f81c498": "append",
}
_GUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def tags_of(row) -> dict:
    """Tag dict from a row; anything else (None, list, string) is 'no tags'. Values become text; a null value becomes ''."""
    t = row.get("tags") if isinstance(row, dict) else None
    if not isinstance(t, dict):
        return {}
    return {str(k): ("" if v is None else str(v)) for k, v in t.items()}


def sub_of(row) -> str:
    s = row.get("subscriptionId") if isinstance(row, dict) else None
    if isinstance(s, str) and s:
        return s.lower()
    parts = str((row or {}).get("id") or "").lower().split("/")
    return parts[parts.index("subscriptions") + 1] if "subscriptions" in parts and parts.index("subscriptions") + 1 < len(parts) else ""


def inventory(rows) -> dict:
    """Whole-estate tag statistics. Keys are folded to lower case; every casing seen is kept."""
    keys: dict = {}
    subs: dict = {}
    types: dict = {}
    total = tagged = 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        total += 1
        t = tags_of(r)
        s = subs.setdefault(sub_of(r), {"total": 0, "tagged": 0, "keys": Counter(), "types": Counter(), "tagged_types": Counter()})
        ty = str(r.get("type") or "").lower()
        s["total"] += 1
        s["types"][ty] += 1
        types.setdefault(ty, [0, 0])[0] += 1
        if t:
            tagged += 1
            s["tagged"] += 1
            s["tagged_types"][ty] += 1
            types[ty][1] += 1
        for k, v in t.items():
            e = keys.setdefault(k.lower(), {"resources": 0, "casings": Counter(), "values": Counter()})
            e["resources"] += 1
            e["casings"][k] += 1
            e["values"][v] += 1
            s["keys"][k.lower()] += 1
    return {"total": total, "tagged": tagged, "keys": keys, "subs": subs, "types": types}


def classify_assignment(row) -> dict | None:
    """Tag-policy assignment details, or None when the definition is not a known built-in tag policy (custom definitions and
    initiatives cannot be classified from the assignment alone, so they are counted separately and never guessed)."""
    if not isinstance(row, dict):
        return None
    m = _GUID.search(str(row.get("definitionId") or ""))
    if (
        not m
        or "policydefinitions" not in str(row.get("definitionId") or "").lower()
        or "policysetdefinitions" in str(row.get("definitionId") or "").lower()
    ):
        return None
    kind = TAG_DEFINITIONS.get(m.group(0).lower())
    if not kind:
        return None
    params = row.get("parameters") if isinstance(row.get("parameters"), dict) else {}
    name = None
    for k, v in params.items():
        if str(k).lower() == "tagname" and isinstance(v, dict) and isinstance(v.get("value"), str) and v["value"]:
            name = v["value"]
    return {
        "id": str(row.get("id") or ""),
        "kind": kind,
        "tag": name,
        "enforced": str(row.get("enforcementMode") or "Default").lower() != "donotenforce",
        "scope": str(row.get("scope") or ""),
    }


def tag_policies(assignments) -> list:
    return [c for c in (classify_assignment(r) for r in assignments) if c]


def scheme(inv: dict, policies: list, share_pct: int = SCHEME_SHARE_PCT) -> dict:
    """The customer's tagging scheme and where it came from. Returns {source, keys, declared, inferred}."""
    declared = sorted({p["tag"].lower() for p in policies if p.get("tag")})
    inferred = (
        sorted(k for k, e in inv["keys"].items() if inv["total"] and 100.0 * e["resources"] / inv["total"] >= share_pct)
        if inv["total"]
        else []
    )
    if declared:
        return {"source": "policy", "keys": declared, "declared": declared, "inferred": inferred}
    if inferred:
        return {"source": "inferred", "keys": inferred, "declared": [], "inferred": inferred}
    return {"source": "none", "keys": [], "declared": [], "inferred": []}


_NORM = re.compile(r"[\s_\-.]+")


def normalise_value(v: str) -> str:
    """Folding used to spot variants of one value: case, surrounding space, and runs of space, underscore, hyphen, dot."""
    return _NORM.sub(" ", v.strip().lower()).strip()


def value_variants(values: Counter, limit: int = 10) -> list:
    """Groups of distinct raw values that fold to the same normalised value. Synonyms (prod vs production) are NOT inferred."""
    groups: dict = {}
    for v, n in values.items():
        groups.setdefault(normalise_value(v), []).append((v, n))
    out = [sorted(g, key=lambda x: (-x[1], x[0])) for g in groups.values() if len(g) > 1]
    out.sort(key=lambda g: (-sum(n for _, n in g), g[0][0]))
    return [[{"value": v, "count": n} for v, n in g] for g in out[:limit]]
