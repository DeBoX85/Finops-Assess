"""Quality gates that guard the design rules, not just behaviour. See docs/QUALITY.md."""

import ast
import json
import pathlib
import re
import sys

import jsonschema
import pytest

from fcat import checks, collectors, config, manifest, render_json
from fcat.snapshot import Snapshot

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "fcat"
checks.load_builtin()


# ---- check metadata and per-check fixtures (every check must be provable offline) ----
@pytest.mark.parametrize("meta", [m for m, _ in checks.REGISTRY], ids=lambda m: m.id)
def test_check_metadata_is_complete(meta):
    assert re.fullmatch(r"[A-Z]{2,5}-[A-Z0-9]{2,6}-\d{2}", meta.id), "id pattern DOMAIN-AREA-NN"
    assert meta.confidence in {"high", "medium", "low"}
    assert meta.savings_basis in {"none", "actual", "list", "estimate"}
    assert meta.run_cost in {"low", "medium", "high"}
    assert meta.validation in {"offline-only", "live"}
    assert meta.framework and meta.permissions and meta.collectors and meta.title
    for c in meta.collectors:
        assert c in collectors.COLLECTORS, f"{meta.id} needs unknown collector {c}"


def test_check_ids_unique():
    ids = [m.id for m, _ in checks.REGISTRY]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(("meta", "fn"), checks.REGISTRY, ids=lambda x: getattr(x, "id", ""))
def test_each_check_has_positive_and_negative_fixture_cases(meta, fn, tmp_path):
    fx = ROOT / "tests" / "fixtures" / "checks" / f"{meta.id}.json"
    assert fx.exists(), f"missing fixture file for {meta.id}"
    cases = json.loads(fx.read_text())["cases"]
    assert any(c["expect_resource_ids"] for c in cases), "needs a case that expects a finding"
    assert any(not c["expect_resource_ids"] for c in cases), "needs a case that expects none"
    for c in cases:
        snap = Snapshot(tmp_path / c["name"].replace(" ", "_"))
        for name, data in c["snapshot"].items():
            snap.save(name, data)
        got = sorted(f.resource_id for f in fn(snap))
        assert got == sorted(c["expect_resource_ids"]), c["name"]


# ---- ARG query lint: constructs the KB says ARG rejects (docs/KB note 02/06; re-verify live) ----
@pytest.mark.parametrize(("name", "kql"), collectors.COLLECTORS.items())
def test_arg_queries_follow_rules(name, kql):
    low = kql.lower()
    assert "order by" in low, "paging must be repeatable"
    assert re.search(r"project[^|]*\bid\b", low) or "summarize" in low, "keep id in output so a skip token is returned"
    assert not re.search(r"\|\s*(take|limit|sample)\b", low), "limit/take/sample disables skip tokens"
    assert "kind=leftanti" not in low.replace(" ", "") and "kind=leftsemi" not in low.replace(" ", "")
    assert "lookup" not in low


# ---- architecture rules ----
def _imports(path):
    tree = ast.parse(path.read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            yield from (a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            yield n.module


def test_network_and_process_access_is_confined():
    allowed_net = {"http.py"}
    for p in SRC.glob("*.py"):
        mods = set(_imports(p))
        if p.name not in allowed_net:
            assert not {m for m in mods if m.startswith(("urllib.request", "http.client", "requests", "httpx", "socket"))}, p.name
        if p.name not in {"manifest.py"}:
            assert "subprocess" not in mods, f"{p.name} must not spawn processes"


def test_no_write_verbs_outside_allowlist_module():
    for p in SRC.glob("*.py"):
        if p.name == "http.py":
            continue
        text = p.read_text()
        assert not re.search(r'["\'](PUT|PATCH|DELETE)["\']', text), p.name


# ---- customer data must not leak into the manifest (counts only) ----
def test_manifest_has_no_ids_or_names(tmp_path):
    snap = Snapshot(tmp_path / "s")
    snap.save("subscriptions", {"rows": [{"id": "/subscriptions/11111111-2222-3333-4444-555555555555", "name": "Contoso-Prod"}]})
    snap.save("unattached_disks", {"rows": []})
    cfg = config.Config(subscriptions=["11111111-2222-3333-4444-555555555555"])
    f, st = checks.run_all(cfg, snap)
    m = manifest.build(cfg, {}, [], st, [], manifest.now(), manifest.now(), manifest.scope_summary(snap))
    blob = json.dumps(m)
    assert "11111111" not in blob and "Contoso" not in blob
    assert m["scope"]["subscriptions"] == 1 and m["config"]["subscriptions_count"] == 1


# ---- report contract ----
def _report(tmp_path):
    snap = Snapshot(tmp_path / "s")
    snap.save("subscriptions", {"rows": []})
    snap.save("unattached_disks", {"rows": [{"id": "/d1", "sizeGB": 8, "skuName": "S"}]})
    cfg = config.Config(checks={"NOPE": False})
    f, st = checks.run_all(cfg, snap)
    m = manifest.build(cfg, {}, [], st, [], manifest.now(), manifest.now(), manifest.scope_summary(snap))
    return render_json.render(tmp_path / "r.json", m, f)


def test_report_matches_json_schema(tmp_path):
    schema = json.loads((ROOT / "docs" / "schema" / "report.schema.json").read_text())
    jsonschema.validate(_report(tmp_path), schema)


def test_schema_rejects_status_without_reason(tmp_path):
    schema = json.loads((ROOT / "docs" / "schema" / "report.schema.json").read_text())
    d = _report(tmp_path)
    d["manifest"]["checks"].append({"id": "X", "status": "not_assessed"})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(d, schema)


def test_report_is_deterministic_apart_from_times(tmp_path):
    a, b = _report(tmp_path), _report(tmp_path)
    for d in (a, b):
        d["manifest"].pop("started"), d["manifest"].pop("ended")
    assert a == b


# ---- config ----
def test_config_load_and_unknown_profile(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[run]\nprofile="quick"\n[domains]\norphaned=false\n[checks]\n"X-1"=false\n')
    c = config.load(p)
    assert c.profile == "quick" and c.domains["orphaned"] is False
    p.write_text('[run]\nprofile="bogus"\n')
    with pytest.raises(ValueError, match="unknown profile"):
        config.load(p)


def test_quick_profile_skips_expensive_checks():
    meta = checks.CheckMeta("A-B-01", "d", "t", ("c",), ("Reader",), run_cost="high")
    ok, why = config.Config(profile="quick").enabled(meta)
    assert not ok and "run cost" in why


# ---- collectors / cli / auth with fakes ----
class _Tok:
    def token(self):
        return "t"


def test_collectors_record_errors_without_stopping(tmp_path):
    from fcat.http import Client, Response

    class T:
        n = 0

        def send(self, *a):
            T.n += 1
            if T.n == 1:
                return Response(403, {}, {"error": {"code": "AuthorizationFailed"}})
            return Response(200, {}, {"data": [{"id": "x"}], "totalRecords": 1})

    errors = []
    snap = Snapshot(tmp_path)
    collectors.collect(Client(_Tok(), T(), sleep=lambda s: None), snap, config.Config(), errors)
    assert errors and "AuthorizationFailed" in errors[0]["error"]
    assert snap.has("management_groups") or snap.has("unattached_disks")


def test_cli_analyze_offline(tmp_path, capsys):
    from fcat import cli

    out = tmp_path / "out"
    Snapshot(out / "snapshot").save("unattached_disks", {"rows": [{"id": "/d"}]})
    cfgp = tmp_path / "c.toml"
    cfgp.write_text('[run]\nprofile="standard"\n')
    assert cli.main(["analyze", "--config", str(cfgp), "--out", str(out)]) == 0
    assert (out / "report.json").exists() and (out / "report.html").exists()
    assert "ORPH-DISK-01=ran" in capsys.readouterr().out


def test_auth_wraps_credential_errors(monkeypatch):
    import types

    from fcat import auth
    from fcat.errors import AuthError

    class Cred:
        def __init__(self, **kw):
            self.kw = kw

        def get_token(self, scope):
            raise RuntimeError("boom")

    mod = types.ModuleType("azure.identity")
    mod.AzureCliCredential = Cred
    monkeypatch.setitem(sys.modules, "azure", types.ModuleType("azure"))
    monkeypatch.setitem(sys.modules, "azure.identity", mod)
    with pytest.raises(AuthError):
        auth.AzCliTokenProvider(tenant_id="t").token()


def test_urllib_transport_against_local_server():
    import http.server
    import threading

    from fcat.http import UrllibTransport

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(429)
            self.send_header("Retry-After", "7")
            self.end_headers()
            self.wfile.write(b'{"e":1}')

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    r = UrllibTransport().send("GET", f"http://127.0.0.1:{srv.server_port}/x", {}, None)
    assert r.status == 429 and r.headers["retry-after"] == "7" and r.body == {"e": 1}


def test_transport_rejects_other_schemes():
    from fcat.errors import BlockedRequest
    from fcat.http import UrllibTransport

    with pytest.raises(BlockedRequest):
        UrllibTransport().send("GET", "file:///etc/passwd", {}, None)
