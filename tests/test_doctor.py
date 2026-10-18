import json

from fcat import cli, doctor
from fcat.errors import AuthError


class Resp:
    def __init__(self, status, body):
        self.status, self.body = status, body


class Calls(list):
    pass


class FakeClient:
    """Answers ARG POSTs by query text: counts per probe, or an HTTP status."""

    def __init__(self, answers):
        self.answers, self.calls = answers, Calls()

    def request(self, method, url, body=None):
        assert method == "POST"
        from fcat.http import CallRecord

        for key, val in self.answers.items():
            if key in body["query"]:
                if isinstance(val, int) and val >= 400:
                    self.calls.append(CallRecord(method, "/arg", val, 0))
                    return Resp(val, {"error": {"code": "X"}})
                self.calls.append(CallRecord(method, "/arg", 200, 0))
                return Resp(200, {"data": [{"n": val}], "totalRecords": 1})
        raise AssertionError(body["query"])


class Tok:
    def __init__(self, fail=False, tid="t"):
        self.fail, self.tid = fail, tid

    def token(self):
        if self.fail:
            raise AuthError("could not get a token from Azure CLI: X")
        return "tok"

    def identity(self):
        return {"tenant_id": self.tid, "principal_type": "user"}


def test_needs_covers_every_check_and_has_no_resource_data():
    from fcat import checks

    checks.load_builtin()
    md = doctor.needs_markdown()
    assert all(m.id in md for m, _ in checks.REGISTRY) and "## Reader" in md and "not assessed" in md


def test_probe_statuses_pass_denied_throttled_unknown():
    c = FakeClient({"advisorresources": 0, "microsoft.resources/subscriptions": 3, "resources | summarize": 403, "managementgroups": 429})
    r = {x["probe"]: x for x in doctor.probe(c, Tok())}
    assert r["token"]["status"] == "pass" and r["identity"]["status"] == "pass"
    assert r["subscriptions_visible"]["status"] == "pass"
    assert r["resources_readable"]["status"] == "not_allowed"
    assert r["management_groups_visible"]["status"] == "throttled"
    assert r["advisor_readable"]["status"] == "unknown"  # zero is not guessed as pass


def test_token_failure_stops_probing_and_identity_gap_is_unknown():
    r = doctor.probe(FakeClient({}), Tok(fail=True))
    assert len(r) == 1 and r[0]["status"] == "not_allowed"
    r = doctor.probe(
        FakeClient({"advisorresources": 1, "subscriptions": 1, "resources | summarize": 1, "managementgroups": 1}), Tok(tid=None)
    )
    assert {x["probe"]: x["status"] for x in r}["identity"] == "unknown"


def test_cli_needs_is_offline(capsys):
    assert cli.main(["doctor", "--needs"]) == 0
    assert "Access F-CAT needs" in capsys.readouterr().out


def test_cli_probe_writes_counts_only(tmp_path, monkeypatch):
    c = FakeClient({"advisorresources": 4, "microsoft.resources/subscriptions": 2, "resources | summarize": 9, "managementgroups": 1})
    monkeypatch.setattr(cli, "AzCliTokenProvider", lambda: Tok())
    monkeypatch.setattr(cli, "Client", lambda tp: c)
    assert cli.main(["doctor", "--out", str(tmp_path / "o")]) == 0
    data = json.loads((tmp_path / "o" / "doctor.json").read_text())
    assert data["calls"] == 4 and all(p["status"] == "pass" for p in data["probes"])
    assert set(data) == {"probes", "calls"}  # counts and statuses only; the tenant id is never written
