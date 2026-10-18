"""Excel report from the same document as the JSON/HTML. Requires openpyxl (optional extra)."""

from openpyxl import Workbook
from openpyxl.styles import Font


def _sheet(wb, title, header, rows):
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append([("" if v is None else v) for v in r])
        for c in ws[ws.max_row]:
            # Resource names and tags are controlled by whoever can create resources in the tenant. A value starting with = + - @ would
            # otherwise be stored as a formula (spreadsheet formula injection, OWASP CSV injection). Force literal text.
            if isinstance(c.value, str) and c.value[:1] in ("=", "+", "-", "@", "\t", "\r"):
                c.data_type = "s"
    ws.freeze_panes = "A2"
    for i, h in enumerate(header, 1):
        ws.column_dimensions[chr(64 + i)].width = max(14, min(60, len(h) + 10))


def render(path, doc):
    m = doc["manifest"]
    wb = Workbook()
    wb.remove(wb.active)
    _sheet(
        wb,
        "Summary",
        ["Item", "Value"],
        [
            ("Tool version", m["tool_version"]),
            ("Git commit", m.get("git_commit")),
            ("Schema", doc["schema_version"]),
            ("Started", m["started"]),
            ("Ended", m["ended"]),
            ("Findings", len(doc["findings"])),
            *[(f"Scope: {k}", "not assessed" if v is None else v) for k, v in m.get("scope", {}).items()],
        ],
    )
    _sheet(
        wb,
        "Checks",
        ["Check", "Status", "Reason", "Findings"],
        [(c["id"], c["status"], c.get("reason"), c.get("findings")) for c in m["checks"]],
    )
    _sheet(
        wb,
        "Findings",
        ["Check", "Severity", "Finding", "Resource"],
        [(f["check_id"], f["severity"], f["message"], f["resource_id"]) for f in doc["findings"]],
    )
    _sheet(
        wb,
        "Catalogue",
        ["ID", "Domain", "Title", "Confidence", "Savings basis", "Run cost", "Framework", "Validation"],
        [
            (c["id"], c["domain"], c["title"], c["confidence"], c["savings_basis"], c["run_cost"], c["framework"], c["validation"])
            for c in doc["check_catalogue"]
        ],
    )
    au = doc.get("audit")
    if au:
        _sheet(
            wb,
            "Audit",
            ["ID", "Result", "What it verifies", "Violations"],
            [(i["id"], "pass" if i["passed"] else "FAIL", i["description"], i["violation_count"]) for i in au["invariants"]]
            + [("", "", "Overall", au["status"]), ("", "", "Report fingerprint", au["report_hash"]), ("", "", "Limits", au["limits"])],
        )
    wb.save(path)
