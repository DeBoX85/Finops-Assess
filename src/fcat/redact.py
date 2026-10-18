"""Redacted reports (threat T-07): replace tenant, subscription, resource group and resource names with short stable pseudonyms
so a report can be shown without exposing customer identifiers. Pseudonyms are sha256(random per-run salt + lowercased value);
the salt is never stored, so they cannot be reversed or compared across runs. The snapshot on disk is NOT redacted.
Limit: free text a check copies from customer data into a message would only be replaced if it equals a name found in the resource id."""

from __future__ import annotations

import hashlib
import secrets

from .checks import fingerprint


def new_salt() -> str:
    return secrets.token_hex(16)


def _p(prefix: str, value: str, salt: str) -> str:
    return f"{prefix}-{hashlib.sha256((salt + value.lower()).encode()).hexdigest()[:8]}"


def resource_id(rid: str, salt: str, names: dict | None = None) -> str:
    """Pseudonymise subscription, resource group and resource names; keep provider and type so the report stays readable."""
    parts = rid.split("/")
    out, i, names = [], 0, names if names is not None else {}
    in_providers = False
    while i < len(parts):
        seg = parts[i]
        low = seg.lower()
        nxt = parts[i + 1] if i + 1 < len(parts) else None
        if low == "subscriptions" and nxt:
            out += [seg, names.setdefault(nxt, _p("sub", nxt, salt))]
            i += 2
        elif low == "resourcegroups" and nxt:
            out += [seg, names.setdefault(nxt, _p("rg", nxt, salt))]
            i += 2
        elif low == "providers" and nxt:
            out += [seg, nxt]  # namespace stays
            in_providers = True
            i += 2
        elif in_providers and nxt is not None:
            out += [seg, names.setdefault(nxt, _p("res", nxt, salt))]  # type stays, name replaced
            i += 2
        else:
            out.append(seg if not (in_providers and seg) else names.setdefault(seg, _p("res", seg, salt)))
            i += 1
    return "/".join(out)


def _scrub(value, names: dict):
    if isinstance(value, str):
        for orig, rep in sorted(names.items(), key=lambda kv: -len(kv[0])):
            if orig and orig.lower() in value.lower():
                value = _ireplace(value, orig, rep)
        return value
    if isinstance(value, dict):
        return {k: _scrub(v, names) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, names) for v in value]
    return value


def _ireplace(text: str, old: str, new: str) -> str:
    low, o, out, i = text.lower(), old.lower(), [], 0
    while True:
        j = low.find(o, i)
        if j < 0:
            out.append(text[i:])
            return "".join(out)
        out += [text[i:j], new]
        i = j + len(old)


def findings(fs, salt: str):
    """Returns new redacted findings with recomputed fingerprints, sorted like the runner sorts them."""
    import copy  # noqa: PLC0415

    out = []
    for f in fs:
        names: dict = {}
        g = copy.deepcopy(f)
        g.resource_id = resource_id(f.resource_id, salt, names)
        g.message = _scrub(g.message, names)
        g.details = _scrub(g.details, names)
        g.fingerprint = fingerprint(g)
        out.append(g)
    out.sort(key=lambda x: (x.check_id, x.resource_id))
    return out


def identity(ident: dict, salt: str) -> dict:
    d = dict(ident or {})
    if d.get("tenant_id"):
        d["tenant_id"] = _p("tenant", str(d["tenant_id"]), salt)
    return d
