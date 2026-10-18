"""Offer / quota ID classification: does Cost Management hold data for this subscription?
Source: Learn "Understand Cost Management data", read 2026-10-18 (VERIFIED for the listed quota IDs).
A quota ID alone is NOT always enough: the same ID is used by several agreement types, and classic CSP is unsupported
while CSP on a Microsoft Customer Agreement is supported. Ambiguous IDs return 'depends' and must be settled by a live probe
(design only, needs a tenant). Unknown IDs return 'unknown', never a guess."""

from __future__ import annotations

SUPPORTED, UNSUPPORTED, DEPENDS, UNKNOWN = "supported", "unsupported", "depends", "unknown"

_TABLE = {
    "enterpriseagreement_2014-09-01": (SUPPORTED, "Enterprise Agreement or Microsoft Customer Agreement (Microsoft Azure Plan)"),
    "msdndevtest_2014-09-01": (SUPPORTED, "Enterprise Dev/Test, MCA Dev/Test or pay-as-you-go Dev/Test"),
    "csp_2015-05-01": (DEPENDS, "CSP: supported when on a Microsoft Customer Agreement Azure plan; classic CSP is NOT supported"),
    "csp_mg_2017-12-01": (DEPENDS, "CSP (MCA via partner listed as supported; classic CSP is not). Quota IDs are shared across agreements"),
    "cspdevtest_2018-05-01": (DEPENDS, "CSP Dev/Test (MCA via partner listed as supported; classic CSP is not)"),
    "msdn_2014-09-01": (SUPPORTED, "MSDN / Visual Studio (historical data may not match invoice)"),
    "pay-as-you-go_2014-09-01": (SUPPORTED, "Pay-as-you-go (data up to 72 h late; no Marketplace or commitment purchases in MOSA)"),
    "mpn_2014-09-01": (SUPPORTED, "Microsoft Cloud Partner Program / Visual Studio Enterprise MPN"),
    "freetrial_2014-09-01": (SUPPORTED, "Free trial (historical data may not match invoice)"),
    "azureinopen_2014-09-01": (SUPPORTED, "Azure in Open (historical data may not match invoice)"),
    "azurepass_2014-09-01": (SUPPORTED, "Azure Pass (historical data may not match invoice)"),
    "sponsored_2016-01-01": (UNSUPPORTED, "Microsoft Azure Sponsorship"),
    "dreamspark_2015-02-01": (UNSUPPORTED, "Azure for Students Starter"),
    "azureforstudents_2018-01-01": (UNSUPPORTED, "Azure for Students"),
    "default_2014-09-01": (UNSUPPORTED, "Support plan"),
}
# UNVERIFIED alias: some tools write the pay-as-you-go ID without hyphens. Not confirmed against live ARG output.
_ALIASES = {"payasyougo_2014-09-01": "pay-as-you-go_2014-09-01"}


def classify(quota_id) -> dict:
    key = (quota_id or "").strip().lower()
    key = _ALIASES.get(key, key)
    if key in _TABLE:
        status, note = _TABLE[key]
        return {"quota_id": quota_id, "cost_management": status, "note": note}
    return {
        "quota_id": quota_id or None,
        "cost_management": UNKNOWN,
        "note": "Quota ID not in the documented list; cost data availability not assessed",
    }
