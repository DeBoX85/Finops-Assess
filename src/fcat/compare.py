"""Run-to-run comparison (backlog 34). Pure offline function over two report.json documents; no Azure access.

Wording is deliberately cautious. A finding that is absent from the newer run is "no longer reported", not "fixed":
the resource may be gone, the check may have changed, or the scope may differ. A finding is only called new or
no longer reported when the check ran in BOTH runs; otherwise the pair is "not comparable, because X" (hard rule 6).
"""

from __future__ import annotations

import json
import pathlib

from .errors import FcatError

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}
VERSION = "0.1"


class CompareError(FcatError):
    pass


def load(path) -> dict:
    try:
        doc = json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError) as e:
        raise CompareError(f"cannot read report {path}: {e}") from e
    if not isinstance(doc, dict) or "findings" not in doc or "manifest" not in doc:
        raise CompareError(f"{path} is not an F-CAT report.json")
    return doc


def _status(doc) -> dict:
    return {c["id"]: c for c in doc["manifest"].get("checks", [])}


def _logic(doc) -> dict:
    out = {}
    for f in doc["findings"]:
        h = (f.get("evidence") or {}).get("logic_hash")
        if h:
            out[f["check_id"]] = h
    return out


def _side(doc) -> dict:
    return {
        "report_hash": (doc.get("audit") or {}).get("report_hash"),
        "audit": (doc.get("audit") or {}).get("status"),
        "started": doc["manifest"].get("started"),
        "tool_version": doc["manifest"].get("tool_version"),
        "findings": len(doc["findings"]),
    }


def compare(old: dict, new: dict) -> dict:
    for label, d in (("older", old), ("newer", new)):
        if d["manifest"].get("redacted"):
            raise CompareError(
                f"the {label} report is redacted: pseudonyms use a new random salt on every run, so two redacted runs cannot be compared. "
                "Compare the unredacted reports instead."
            )
    warnings = []
    for label, d in (("older", old), ("newer", new)):
        if (d.get("audit") or {}).get("status") != "pass":
            warnings.append(f"the {label} report did not pass its self-audit; treat the comparison with caution")

    def _scope_core(d):
        sc = d["manifest"].get("scope") or {}
        return {k: sc.get(k) for k in ("subscriptions", "management_groups")}

    if _scope_core(old) != _scope_core(new):  # resource counts change with the estate and are not a scope change
        warnings.append(
            "the two runs saw a different number of subscriptions or management groups, so changes may come from scope, not from the estate"
        )
    if (old["manifest"].get("config") or {}).get("subscriptions_count") != (new["manifest"].get("config") or {}).get("subscriptions_count"):
        warnings.append("the configured subscription lists differ in size")
    warnings.append("the tool cannot confirm that both reports describe the same tenant; check that yourself")
    if (old["manifest"].get("started") or "") > (new["manifest"].get("started") or ""):
        warnings.append("the first report is newer than the second; the comparison treats the first as the baseline anyway")

    so, sn = _status(old), _status(new)
    lo, ln = _logic(old), _logic(new)
    both_ran = {cid for cid in so if so[cid]["status"] == "ran" and sn.get(cid, {}).get("status") == "ran"}
    not_comparable = []
    for cid in sorted(set(so) | set(sn)):
        if cid in both_ran:
            continue
        a, b = so.get(cid, {}), sn.get(cid, {})
        not_comparable.append(
            {
                "check_id": cid,
                "older": a.get("status", "absent"),
                "newer": b.get("status", "absent"),
                "reason": f"not comparable, because the check was '{a.get('status', 'absent')}' in the older run and '{b.get('status', 'absent')}' in the newer run",
            }
        )

    fo = {(f["check_id"], f["resource_id"]): f for f in old["findings"]}
    fn = {(f["check_id"], f["resource_id"]): f for f in new["findings"]}
    items = []
    for key in sorted(set(fo) | set(fn)):
        cid, rid = key
        if cid not in both_ran:
            continue
        a, b = fo.get(key), fn.get(key)
        assert a or b  # every key comes from one of the two maps
        rule_changed = bool(lo.get(cid) and ln.get(cid) and lo[cid] != ln[cid])
        if a and not b:
            state, sev, msg = "no_longer_reported", a["severity"], a["message"]
        elif b and not a:
            state, sev, msg = "new", b["severity"], b["message"]
        elif a and b and a["fingerprint"] == b["fingerprint"] and a["severity"] == b["severity"]:
            state, sev, msg = "unchanged", b["severity"], b["message"]
        else:
            assert a and b  # both sides exist here
            so_, sn_ = SEVERITY_ORDER.get(a["severity"], 0), SEVERITY_ORDER.get(b["severity"], 0)
            state = "worse" if sn_ > so_ else "better" if sn_ < so_ else "changed"
            sev, msg = b["severity"], b["message"]
        item = {"state": state, "check_id": cid, "resource_id": rid, "severity": sev, "message": msg, "rule_changed": rule_changed}
        if state in {"worse", "better", "changed"}:
            item["older_severity"] = a["severity"]
            changed = sorted(
                k
                for k in set(a.get("details", {})) | set(b.get("details", {}))
                if a.get("details", {}).get(k) != b.get("details", {}).get(k)
            )
            item["changed_detail_keys"] = changed
        items.append(item)

    counts = {k: sum(1 for i in items if i["state"] == k) for k in ("new", "no_longer_reported", "worse", "better", "changed", "unchanged")}
    counts["rule_changed_items"] = sum(1 for i in items if i["rule_changed"])
    counts["checks_not_comparable"] = len(not_comparable)
    if counts["rule_changed_items"]:
        warnings.append(
            "for some checks the rule text changed between runs; differences on those lines may come from the rule, not the estate"
        )
    return {
        "compare_version": VERSION,
        "older": _side(old),
        "newer": _side(new),
        "warnings": warnings,
        "counts": counts,
        "items": items,
        "not_comparable": not_comparable,
    }


def markdown(result: dict) -> str:
    c = result["counts"]
    lines = [
        "# Changes since the previous run",
        "",
        f"Older report: {result['older']['started']} (fingerprint {result['older']['report_hash']}). "
        f"Newer report: {result['newer']['started']} (fingerprint {result['newer']['report_hash']}).",
        "",
        f"New: {c['new']}. No longer reported: {c['no_longer_reported']}. Worse: {c['worse']}. Better: {c['better']}. "
        f"Changed: {c['changed']}. Unchanged: {c['unchanged']}. Checks not comparable: {c['checks_not_comparable']}.",
        "",
        "No longer reported does not prove a fix: the resource may be gone, the rule may have changed, or the scope may differ.",
        "",
    ]
    if result["warnings"]:
        lines += ["## Read this first", ""] + [f"- {w}" for w in result["warnings"]] + [""]
    for state, title in (
        ("new", "New"),
        ("worse", "Worse"),
        ("changed", "Changed"),
        ("better", "Better"),
        ("no_longer_reported", "No longer reported"),
    ):
        rows = [i for i in result["items"] if i["state"] == state]
        if rows:
            lines += [f"## {title} ({len(rows)})", ""]
            lines += [
                f"- {i['check_id']} {i['resource_id']} ({i['severity']}){' [rule changed]' if i['rule_changed'] else ''}: {i['message']}"
                for i in rows
            ]
            lines.append("")
    if result["not_comparable"]:
        lines += ["## Not comparable", ""] + [f"- {n['check_id']}: {n['reason']}" for n in result["not_comparable"]] + [""]
    return "\n".join(lines)
