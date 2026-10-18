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
    assert by["ORPH-ASP-01"] == {"asp-empty"}
    assert golden["audit"]["status"] == "pass" and len(golden["findings"]) == 68 + 5 + 3
