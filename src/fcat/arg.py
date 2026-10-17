"""Azure Resource Graph collector. REST: POST /providers/Microsoft.ResourceGraph/resources.
Paging rules from Learn (read 2026-10-17): max 1000 rows per page; follow $skipToken; no skipToken if the query
uses limit/take/sample, or all output columns are dynamic/null; keep `id` in the output; each page costs quota.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .errors import IncompleteResult, FcatError

URL = "https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2022-10-01"

@dataclass
class QueryResult:
    rows: list
    total_records: int | None
    pages: int
    warnings: list = field(default_factory=list)

def query(client, kql: str, subscriptions: list[str] | None = None, management_groups: list[str] | None = None, page_size: int = 1000) -> QueryResult:
    if subscriptions and management_groups:
        raise FcatError("subscriptions and managementGroups cannot be combined")
    warnings = []
    if "order by" not in kql.lower():
        warnings.append("query has no 'order by': paging is not repeatable")
    rows, skip, pages, total = [], None, 0, None
    while True:
        body = {"query": kql, "options": {"$top": page_size}}
        if skip:
            body["options"]["$skipToken"] = skip
        if subscriptions:
            body["subscriptions"] = subscriptions
        if management_groups:
            body["managementGroups"] = management_groups
        r = client.request("POST", URL, body)
        if r.status != 200:
            code = (r.body or {}).get("error", {}).get("code") if isinstance(r.body, dict) else None
            raise FcatError(f"ARG query failed: HTTP {r.status} {code or ''}".strip())
        b = r.body or {}
        pages += 1
        got = b.get("data") or []
        rows.extend(got)
        total = b.get("totalRecords", total)
        client.calls[-1].rows = len(got)
        skip = b.get("$skipToken")
        if not skip:
            if b.get("resultTruncated") in (True, "true") or (total is not None and len(rows) < total):
                raise IncompleteResult(f"ARG result truncated without a skip token ({len(rows)} of {total} rows); "
                                       "check for limit/take/sample or all-dynamic columns, and keep 'id' in the output")
            break
    return QueryResult(rows, total, pages, warnings)
