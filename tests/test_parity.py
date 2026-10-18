"""docs/PARITY.md must not name checks that do not exist, and every DONE-OFFLINE row must name at least one."""

import pathlib
import re

from fcat import checks

checks.load_builtin()
TEXT = (pathlib.Path(__file__).resolve().parent.parent / "docs" / "PARITY.md").read_text()
IDS = {m.id for m, _ in checks.REGISTRY}


def test_named_check_ids_exist():
    named = set(re.findall(r"\b[A-Z]{2,5}-[A-Z0-9]{2,6}-\d{2}\b", TEXT))
    assert named and named <= IDS, named - IDS


def test_done_rows_name_a_check():
    for line in TEXT.splitlines():
        if line.startswith("|") and "DONE-OFFLINE" in line and "Status" not in line:
            assert re.search(r"\b[A-Z]{2,5}-[A-Z0-9]{2,6}-\d{2}\b", line), line


def test_every_registered_check_with_workbook_parity_is_listed():
    unlisted = {i for i in IDS if i not in TEXT}
    assert not (unlisted - {"BILL-OFFER-01"}), unlisted
