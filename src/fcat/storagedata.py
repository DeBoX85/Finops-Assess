"""Storage lifecycle policy collector (opt-in `[run] storage_apis = true`), backlog 44.

Why REST and not Resource Graph: Learn's Resource Graph table reference does not list the storage management policy type (KB 18, read 2026-10-21).
What is used instead: one GET per eligible storage account, which is already allowed by the read-only allowlist (GET on management.azure.com), so
no allowlist change is needed. Learn (REST reference Management Policies - Get, api-version 2026-09-01, read 2026-10-21):
  GET {account id}/managementPolicies/default?api-version=...  200 returns properties.policy.rules[] (name, enabled, type Lifecycle, definition).
  Other status codes return an ErrorResponse {error: {code, message}}.
UNVERIFIED live: the status and error code returned when an account has NO policy (assumed 404 with code ManagementPolicyNotFound). Anything else
that is not a 200 is recorded as an error for that account, never as 'no policy'.
Call volume: one read per eligible account. Learn throttling page (read 2026-10-21): storage account management reads 800 per 5 minutes per
subscription per region, so the cap below keeps a run well inside that for one region."""

from __future__ import annotations

import re

API = "2026-09-01"
BASE = "https://management.azure.com"
MAX_ACCOUNTS = 1000
ELIGIBLE_KINDS = ("storagev2", "blockblobstorage")  # same set as OPT-STORLC-01
NO_POLICY_CODE = "managementpolicynotfound"  # UNVERIFIED live
_ID = re.compile(r"^/subscriptions/[^/\s]+/resourcegroups/[^/\s]+/providers/microsoft\.storage/storageaccounts/[a-z0-9]{3,24}$", re.I)


def policy_url(account_id):
    return f"{BASE}{account_id}/managementPolicies/default?api-version={API}"


def _read_one(client, account_id):
    """Returns one row: status 'present' (with rule counts), 'none' (documented-by-assumption 'not found' reply) or 'error: ...'."""
    r = client.request("GET", policy_url(account_id))
    row = {"id": account_id.lower(), "status": "", "ruleCount": None, "enabledRuleCount": None}
    if r.status == 200:
        props = r.body.get("properties") if isinstance(r.body, dict) else None
        pol = props.get("policy") if isinstance(props, dict) else None
        rules = pol.get("rules") if isinstance(pol, dict) else None
        if not isinstance(rules, list):
            row["status"] = "error: 200 reply without a rules list"
            return row
        valid = [x for x in rules if isinstance(x, dict)]
        row.update(status="present", ruleCount=len(valid), enabledRuleCount=sum(1 for x in valid if x.get("enabled") is not False))
        return row
    code = ""
    if isinstance(r.body, dict) and isinstance(r.body.get("error"), dict):
        code = str(r.body["error"].get("code") or "").lower()
    if r.status == 404 and code == NO_POLICY_CODE:
        row["status"] = "none"
    else:
        row["status"] = f"error: HTTP {r.status}" + (f" {code}" if code else "")
    return row


def collect_storage_lifecycle(client, snapshot, config, errors: list):
    """Writes snapshot 'storage_lifecycle': {'rows', 'eligible', 'queried', 'truncated', 'api_version'}. Needs the 'storage_accounts' inventory.
    Nothing is written when no account could be read at all, so the check says 'not assessed' (lesson M-008)."""
    if not snapshot.has("storage_accounts"):
        errors.append(
            {
                "collector": "storage_lifecycle",
                "error": "storage account inventory (storage_accounts) is missing, so no account could be selected",
            }
        )
        return
    accounts = sorted(
        {
            r["id"]
            for r in (snapshot.load("storage_accounts") or {}).get("rows", [])
            if isinstance(r, dict)
            and isinstance(r.get("id"), str)
            and _ID.match(r["id"])
            and str(r.get("kind") or "").lower() in ELIGIBLE_KINDS
        }
    )
    if not accounts:
        return  # nothing to read; the check will find no eligible accounts either
    todo = accounts[:MAX_ACCOUNTS]
    rows = [_read_one(client, a) for a in todo]
    bad = sum(1 for r in rows if r["status"].startswith("error"))
    if bad:
        errors.append(
            {
                "collector": "storage_lifecycle",
                "error": f"{bad} of {len(rows)} storage accounts could not be read (first: {next(r['status'] for r in rows if r['status'].startswith('error'))})",
            }
        )
    if bad == len(rows):
        return
    snapshot.save(
        "storage_lifecycle",
        {"rows": rows, "eligible": len(accounts), "queried": len(todo), "truncated": len(accounts) > len(todo), "api_version": API},
    )
