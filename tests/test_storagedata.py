"""Storage lifecycle collector (src/fcat/storagedata.py) and OPT-STORLC-01: exact answers only, no guessing, opt-in switch."""

import pytest

from fcat import checks, collectors, config, storagedata
from fcat.checks import NotAssessed
from fcat.http import Client, Response
from fcat.snapshot import Snapshot

checks.load_builtin()
SUB = "/subscriptions/s1/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/"


class Tok:
    def token(self):
        return "t"

    def identity(self):
        return {}


class Fake:
    def __init__(self, *responses):
        self.responses, self.sent = list(responses), []

    def send(self, method, url, headers, body):
        self.sent.append((method, url))
        return self.responses.pop(0)


def client(*responses):
    t = Fake(*responses)
    return Client(Tok(), transport=t, sleep=lambda s: None), t


def ok(rules):
    return Response(200, {}, {"properties": {"policy": {"rules": rules}}})


def missing():
    return Response(404, {}, {"error": {"code": "ManagementPolicyNotFound", "message": "x"}})


def snap_with(tmp_path, *rows):
    s = Snapshot(tmp_path / "snap")
    s.save("storage_accounts", {"rows": list(rows)})
    return s


def acct(name, kind="StorageV2"):
    return {"id": SUB + name, "kind": kind, "skuName": "Standard_LRS"}


def test_url_is_a_get_on_the_documented_path_and_passes_the_allowlist():
    c, t = client(ok([]))
    storagedata._read_one(c, SUB + "stone")
    method, url = t.sent[0]
    assert method == "GET" and url.endswith("/storageAccounts/stone/managementPolicies/default?api-version=2026-09-01")


def test_present_none_and_error_are_told_apart():
    c, _ = client(
        ok([{"enabled": True}, {"enabled": False}, {}, "junk"]),
        missing(),
        Response(403, {}, {"error": {"code": "AuthorizationFailed"}}),
        Response(404, {}, {}),
        Response(200, {}, {"properties": {}}),
    )
    a = storagedata._read_one(c, SUB + "aaa")
    assert (a["status"], a["ruleCount"], a["enabledRuleCount"]) == (
        "present",
        3,
        2,
    )  # missing 'enabled' counts as enabled; non-dict ignored
    assert storagedata._read_one(c, SUB + "bbb")["status"] == "none"
    assert storagedata._read_one(c, SUB + "ccc")["status"] == "error: HTTP 403 authorizationfailed"
    assert storagedata._read_one(c, SUB + "ddd")["status"] == "error: HTTP 404"  # a 404 WITHOUT the not-found code is not 'no policy'
    assert storagedata._read_one(c, SUB + "eee")["status"].startswith("error: 200")


def test_collect_reads_only_eligible_well_formed_accounts(tmp_path):
    s = snap_with(
        tmp_path,
        acct("stone"),
        acct("sfile", "FileStorage"),
        acct("stwo", "BlockBlobStorage"),
        {"id": "/not/an/account", "kind": "StorageV2"},
        {"id": 5},
    )
    c, t = client(ok([{"enabled": True}]), missing())
    errs: list = []
    storagedata.collect_storage_lifecycle(c, s, config.Config(), errs)
    d = s.load("storage_lifecycle")
    assert [r["status"] for r in d["rows"]] == ["present", "none"] and d["eligible"] == 2 and d["truncated"] is False and not errs
    assert len(t.sent) == 2


def test_nothing_is_written_when_every_read_failed(tmp_path):
    s = snap_with(tmp_path, acct("stone"))
    c, _ = client(Response(403, {}, {}))
    errs: list = []
    storagedata.collect_storage_lifecycle(c, s, config.Config(), errs)
    assert not s.has("storage_lifecycle") and errs and "1 of 1" in errs[0]["error"]


def test_missing_inventory_and_empty_inventory(tmp_path):
    errs: list = []
    storagedata.collect_storage_lifecycle(client()[0], Snapshot(tmp_path / "a"), config.Config(), errs)
    assert errs and "missing" in errs[0]["error"]
    s = snap_with(tmp_path, acct("sfile", "FileStorage"))
    errs = []
    storagedata.collect_storage_lifecycle(client()[0], s, config.Config(), errs)
    assert not errs and not s.has("storage_lifecycle")


def test_cap_marks_the_snapshot_truncated(tmp_path, monkeypatch):
    monkeypatch.setattr(storagedata, "MAX_ACCOUNTS", 1)
    s = snap_with(tmp_path, acct("stone"), acct("stwo"))
    c, _ = client(missing())
    storagedata.collect_storage_lifecycle(c, s, config.Config(), [])
    d = s.load("storage_lifecycle")
    assert d["truncated"] is True and d["queried"] == 1 and d["eligible"] == 2


def run_check(tmp_path, lifecycle, *accounts):
    s = snap_with(tmp_path, *accounts)
    if lifecycle is not None:
        s.save("storage_lifecycle", lifecycle)
    meta = next(m for m, _ in checks.REGISTRY if m.id == "OPT-STORLC-01")
    fn = next(f for m, f in checks.REGISTRY if m.id == "OPT-STORLC-01")
    return meta, list(fn(s))


@pytest.mark.parametrize(
    "rows,truncated",
    [
        ([], False),  # no answers at all
        ([{"id": (SUB + "stone").lower(), "status": "error: HTTP 403", "enabledRuleCount": None}], False),
        ([{"id": (SUB + "stone").lower(), "status": "present", "enabledRuleCount": None}], False),  # present but count unknown
        ([{"id": (SUB + "stone").lower(), "status": "present", "enabledRuleCount": True}], False),  # bool is not a count
        ([{"id": (SUB + "stone").lower(), "status": "none"}], True),  # cut off at the cap
    ],
)
def test_check_refuses_to_decide_without_a_definite_answer(tmp_path, rows, truncated):
    with pytest.raises(NotAssessed):
        run_check(tmp_path, {"rows": rows, "truncated": truncated}, acct("stone"))


def test_check_flags_no_policy_and_all_disabled_but_not_a_working_policy(tmp_path):
    rows = [
        {"id": (SUB + "a1").lower(), "status": "none"},
        {"id": (SUB + "a2").lower(), "status": "present", "ruleCount": 1, "enabledRuleCount": 0},
        {"id": (SUB + "a3").lower(), "status": "present", "ruleCount": 1, "enabledRuleCount": 1},
    ]
    _, fs = run_check(tmp_path, {"rows": rows, "truncated": False}, acct("a1"), acct("a2"), acct("a3"))
    assert sorted(f.resource_id.rsplit("/", 1)[-1] for f in fs) == ["a1", "a2"]


def test_id_match_is_case_insensitive(tmp_path):
    rows = [{"id": (SUB + "AbC").lower(), "status": "none"}]
    _, fs = run_check(tmp_path, {"rows": rows, "truncated": False}, acct("AbC"))
    assert len(fs) == 1


def test_switch_is_wired():
    assert "storage_lifecycle" in collectors.REST_COLLECTORS and "storage_lifecycle" not in collectors.COLLECTORS
    assert checks.OPT_IN_SWITCH["storage_lifecycle"] == "[run] storage_apis = true"
    assert config.Config().storage_apis is False and config.Config(storage_apis=True).as_dict()["storage_apis"] is True


def test_config_validates_the_switch(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("[run]\nstorage_apis = true\n")
    assert config.load(p).storage_apis is True
    p.write_text('[run]\nstorage_apis = "yes"\n')
    with pytest.raises(ValueError, match="storage_apis"):
        config.load(p)


def test_collect_calls_storagedata_only_when_switched_on(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(storagedata, "collect_storage_lifecycle", lambda *a, **k: seen.append(1))
    monkeypatch.setattr(collectors, "COLLECTORS", {})
    for on in (False, True):
        collectors.collect(client()[0], Snapshot(tmp_path / f"s{on}"), config.Config(storage_apis=on), [])
    assert seen == [1]
