"""Approval (golden) test on the synthetic estate. Synthetic data proves stability, not realism (docs/AUDIT.md layer E).
If this fails after a change, explain the diff in the changelog and re-approve with: python scripts/make_synthetic.py --approve"""

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("make_synthetic", ROOT / "scripts" / "make_synthetic.py")
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)

EXCLUDED = {"disk-100", "disk-101", "disk-102", "disk-103"}  # ActiveSAS, ASR replica, ASR seed (two tag spellings)


def test_synthetic_snapshot_is_in_sync_with_generator(tmp_path):
    for name, rows in ms.estate().items():
        stored = json.loads((ms.SNAP / f"{name}.json").read_text())
        assert stored["rows"] == rows, f"{name}: run python scripts/make_synthetic.py"


def test_report_matches_golden(tmp_path):
    rc, doc = ms.normalised_report(tmp_path)
    golden = json.loads(ms.GOLDEN.read_text())
    assert rc == 0
    assert doc == golden, "report changed: review, explain in the changelog, then re-approve"


def test_golden_is_correct_by_independent_derivation():
    """Expected findings derived by hand from the estate definition, not from the check code."""
    golden = json.loads(ms.GOLDEN.read_text())
    got = {f["resource_id"].rsplit("/", 1)[-1] for f in golden["findings"] if f["check_id"] == "ORPH-DISK-01"}
    bill = {
        f["resource_id"].rsplit("/", 1)[-1]: f["details"]["cost_management"] for f in golden["findings"] if f["check_id"] == "BILL-OFFER-01"
    }
    assert bill == {"sub-synth-2": "depends", "sub-synth-3": "unsupported"}  # sub 1 is Enterprise Agreement: supported, no finding
    expected = {f"disk-{n:03d}" for n in list(range(1, 61)) + [104, 105, 106, 107, 108, 109]}
    assert got == expected and not (got & EXCLUDED)
    by = {}
    for f in golden["findings"]:
        by.setdefault(f["check_id"], set()).add(f["resource_id"].rsplit("/", 1)[-1])
    # hand-derived from scripts/make_synthetic.py: attached/used/free-tier/unknown-count rows must NOT appear
    assert by["ORPH-PIP-01"] == {"pip-orphan-1", "pip-orphan-2", "pip-via-orphan-nic"}
    assert by["ORPH-NIC-01"] == {"nic-orphan"}
    assert by["ORPH-NSG-01"] == {"nsg-orphan", "nsg-absent"}
    assert by["IDLE-VMSTOP-01"] == {"vm-stopped"}
    assert by["ORPH-LB-01"] == {"lb-nopool"}
    assert by["ORPH-AGW-01"] == {"agw-empty"}
    assert by["ORPH-EPOOL-01"] == {"pool-empty"}
    assert by["ORPH-VGW-01"] == {"gw-idle"}  # p2s and connected (case-insensitive id match) gateways excluded
    assert by["ORPH-NAT-01"] == {"nat-orphan"}
    assert by["ORPH-DDOS-01"] == {"ddos-unused"}
    assert by["ORPH-ERC-01"] == {"erc-pending"}
    assert by["MON-LAWCAP-01"] == {"law-nocap"}  # capped and Free skipped
    assert by["MON-AICLS-01"] == {"ai-old"}
    assert by["SEC-DEFDEV-01"] == {"VirtualMachines"}  # only the Standard plan on the DevTest subscription
    assert by["ORPH-SNAP-01"] == {"snap-old"}  # 122 days old at the fixed collection time; the others are 5 and 1 days
    assert by["ORPH-SNAP-02"] == {"snap-new-premium"}
    assert by["ORPH-SNAP-03"] == {"snap-orphan-src"}
    assert by["MOD-STORV1-01"] == {"stlegacy"}
    assert by["IDLE-VMDISK-01"] == {"vm-stopped"}  # case-insensitive disk id match; vm-dealloc has a non-premium disk
    assert by["ORPH-PDNS-01"] == {"privatelink.unused.example"}
    assert by["ORPH-PE-01"] == {"pe-dead"}
    assert by["ORPH-ASP-01"] == {"asp-empty"}
    # batch 5, hand-derived: Basic LB and Basic IP also count under the retirement checks; v1 gateway; VHD-backed VM; Windows and SQL PAYG outside Dev/Test
    # (win-ahb, sql-ahub, linux-1, win-dev and sql-dev must NOT appear); only the user autoscale pool; only the open Advisor recommendation
    assert by["MOD-LBBAS-01"] == {"lb-basic"}
    assert by["MOD-PIPBAS-01"] == {"pip-orphan-2"}
    assert by["MOD-AGWV1-01"] == {"agw-v1"}
    assert by["MOD-VMUNMG-01"] == {"vm-unmanaged"}
    assert by["LIC-AHBWIN-01"] == {"win-payg"}
    # Hybrid Benefit VMs: 2 vCPUs (< 8) is reported; 16 vCPUs is not; a size missing from the lookup is skipped, never guessed
    assert by["LIC-AHBVCP-01"] == {"win-ahb"}
    assert by["LIC-AHBSQL-01"] == {"sql-payg"}
    assert by["OPT-AKSSPT-01"] == {"apps"}
    assert by["ADV-COST-01"] == {"rec-resize"}  # commitment advice is NOT repeated here
    # open reservation, savings plan and renewal advice; the completed reservation item must NOT appear
    assert by["RATE-ADVCOM-01"] == {"rec-ri", "rec-sp", "rec-renew"}
    # batch 6, hand-derived: stale backup item; GRS vault only in the Dev/Test subscription; 240 h / 4 h interval = 60 copies; workspace without pools;
    # Premium firewall whose policy has IDPS Off and no TLS (the Alert one must NOT appear)
    assert by["IDLE-BKP-01"] == {"vm-old"}
    assert by["OPT-VAULT-01"] == {"vault-dev-grs"}
    assert by["OPT-COSBKP-01"] == {"cosmos-many-copies"}
    assert by["ORPH-SYN-01"] == {"syn-empty"}
    assert by["OPT-FWPREM-01"] == {"fw-premium-idle"}
    # batch 7, hand-derived: running dev VM without an enabled schedule (the one with a schedule must NOT appear); a staging-named subscription on an EA
    # offer (the Dev/Test one must NOT appear); premium disk and GRS storage in the Dev/Test subscription; two accounts with no lifecycle rules (the
    # one with 2 rules and the legacy kind must NOT appear); the empty availability set
    assert by["IDLE-VMSHUT-01"] == {"vm-dev-noshut"}
    assert by["OPT-DEVOFF-01"] == {"sub-synth-5"}
    assert by["OPT-DTSTOR-01"] == {"dev-prem", "stdevgrs"}
    assert by["OPT-STORLC-01"] == {"stv2nolc", "stdevgrs"}
    assert by["ORPH-AVSET-01"] == {"as-empty"}
    # 2026-05-01 to 2026-10-01 = 153 days (31+30+31+31+30) is over 90; 2026-09-15 is 16 days and must NOT appear
    assert by["IDLE-VMDEAL-01"] == {"vm-dealloc"}
    # cost reconciliation: sub 1 has 1000 USD, 150 on a resource missing from the id list and 50 without id = 20 percent (over the 5 percent
    # threshold); sub 2 has everything known and must NOT appear
    assert by["COST-UNMAP-01"] == {"sub-synth-1"}
    assert (
        golden["audit"]["status"] == "pass"
        and len(golden["findings"]) == 68 + 5 + 3 + 7 + 3 + 7 + 2 + 6 + 5 + 8 + 7 + 1 + 1 + 2 + 2 + 1 + 1 + 1 + 3 + 1
    )


def test_tag_governance_findings_match_hand_derivation():
    """Derived by hand from scripts/make_synthetic.py (tag_inventory, container_tags, policy_assignments, policy_states)."""
    golden = json.loads(ms.GOLDEN.read_text())
    got = {}
    for f in golden["findings"]:
        got.setdefault(f["check_id"], {})[f["resource_id"]] = f
    assert set(got["TAG-DISC-01"]) == {"tags:scheme"} and "(policy): env" in got["TAG-DISC-01"]["tags:scheme"]["message"]
    # sub 2: 8 of 10 lack env (80 percent). Sub 1 is 4 of 20 (20 percent, under the 25 percent gap). Sub 3 has 4 resources (under the minimum).
    assert (
        set(got["TAG-COV-01"]) == {"/subscriptions/sub-synth-2"} and "8 of 10" in got["TAG-COV-01"]["/subscriptions/sub-synth-2"]["message"]
    )
    assert set(got["TAG-CASE-01"]) == {"tag:env"} and set(got["TAG-VAL-01"]) == {"tag:env"}
    assert set(got["TAG-RG-01"]) == {
        "/subscriptions/sub-synth-1/resourceGroups/rg-synth",
        "/subscriptions/sub-synth-2/resourceGroups/rg-synth",
    }
    assert "POL-TAG-01" not in got  # an enforced require-tag assignment exists
    assert set(got["POL-TAGMOD-01"]) == {"policy:tags"}
    (compl,) = got["POL-COMPL-01"].values()
    assert "15 of 34" in compl["message"] and "44%" in compl["message"]


def test_budget_anomaly_export_findings_match_hand_derivation():
    """Derived by hand from scripts/make_synthetic.py (budgets, anomaly_rules, cost_exports; collected_at 2026-10-01)."""
    golden = json.loads(ms.GOLDEN.read_text())
    got = {}
    for f in golden["findings"]:
        got.setdefault(f["check_id"], set()).add(f["resource_id"])
    s = "/subscriptions/sub-synth-"
    assert got["BUD-COVER-01"] == {s + "3"}  # subs 1 and 2 have budgets
    assert got["BUD-ALERT-01"] == {s + "1/providers/Microsoft.Consumption/budgets/b-old"}  # enabled notification without a recipient
    assert got["BUD-EXP-01"] == {s + "1/providers/Microsoft.Consumption/budgets/b-old"}  # ended 2026-06-30, before 2026-10-01
    assert got["BUD-FCST-01"] == {s + "2"}  # sub 1 has a forecast alert on b-main; sub 3 has no budget so it is not judged here
    assert got["ALR-ANOM-01"] == {s + "2", s + "3"}  # sub 1 enabled; sub 2 none; sub 3 disabled
    assert got["EXP-CFG-01"] == {s + "1/providers/Microsoft.CostManagement/exports/daily-actual"}  # last run Failed


def test_scope_line_counts_match_hand_derivation():
    """From the inventory_counts rows of the synthetic estate: 20+10+40+6+4 = 80 resources, 3 types, 3 regions (northeurope, swedencentral, westeurope)."""
    scope = json.loads(ms.GOLDEN.read_text())["manifest"]["scope"]
    assert (scope["resources"], scope["resource_types"], scope["regions"]) == (80, 3, 3)
