"""Live smoke tests: READ-ONLY, need `az login` to the test tenant and FCAT_LIVE=1. Skipped by default.
Run: FCAT_LIVE=1 pytest -m live. See docs/QUALITY.md gate G2. Canary resources are created by the owner, never by the tool."""

import os

import pytest

pytestmark = pytest.mark.live
if os.environ.get("FCAT_LIVE") != "1":
    pytest.skip("set FCAT_LIVE=1 to run live tests", allow_module_level=True)


def test_every_collector_query_is_accepted_by_arg():
    from fcat import arg, collectors
    from fcat.auth import AzCliTokenProvider
    from fcat.http import Client

    client = Client(AzCliTokenProvider())
    for name, kql in collectors.COLLECTORS.items():
        res = arg.query(client, kql)
        assert res.pages >= 1, name


def test_canary_unattached_disk_is_found():
    """Owner creates a tagged unattached disk named fcat-canary-disk in the test tenant (small cost)."""
    from fcat import arg, collectors
    from fcat.auth import AzCliTokenProvider
    from fcat.http import Client

    rows = arg.query(Client(AzCliTokenProvider()), collectors.KQL_UNATTACHED_DISKS).rows
    assert any(r["name"] == "fcat-canary-disk" for r in rows)
