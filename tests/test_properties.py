"""Property-based tests (Hypothesis). They state rules that must hold for ALL inputs, then let Hypothesis hunt for counterexamples.
Profiles: the default 'gate' profile is deterministic (derandomize, no database) so a gate run is repeatable; set HYPOTHESIS_PROFILE=explore
for a longer random search (more examples, fresh seeds). Hypothesis docs read 2026-10-21: https://hypothesis.readthedocs.io/en/latest/reference/api.html"""

import json
import math
import os
import pathlib
import string
import urllib.request

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from fcat import arg, compare, http, maturity, redact
from fcat.checks import Finding, fingerprint
from fcat.errors import BlockedRequest

settings.register_profile(
    "gate", derandomize=True, database=None, deadline=None, max_examples=150, suppress_health_check=[HealthCheck.too_slow]
)
settings.register_profile("explore", database=None, deadline=None, max_examples=3000, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "gate"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = json.loads((ROOT / "tests" / "golden" / "report.json").read_text())


class Tok:
    def token(self):
        return "t"


class Boom:
    """Transport that fails the test if anything is sent: used where a request must be refused before it leaves."""

    def send(self, *a):
        raise AssertionError("a blocked request reached the transport")


class Script:
    def __init__(self, responses):
        self.r = list(responses)
        self.sent = []

    def send(self, method, url, headers, body):
        self.sent.append((method, url))
        return self.r.pop(0)


# ---- 1. read-only allowlist -------------------------------------------------------------------------------------------------------------
HOST = "https://management.azure.com"
VERBS = st.sampled_from(["PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT", "LOCK", "PURGE"])
SEG = st.sampled_from(
    [
        "subscriptions",
        "resourceGroups",
        "providers",
        "Microsoft.Compute",
        "virtualMachines",
        "start",
        "delete",
        "write",
        "listKeys",
        "action",
    ]
) | st.text(alphabet=string.ascii_letters + string.digits + "-_.", min_size=1, max_size=8)


@given(verb=VERBS, segs=st.lists(SEG, min_size=0, max_size=6))
def test_no_verb_other_than_get_and_post_is_ever_sent(verb, segs):
    c = http.Client(Tok(), Boom(), sleep=lambda s: None)
    with pytest.raises(BlockedRequest):
        c.request(verb, HOST + "/" + "/".join(segs) + "?api-version=2022-01-01")


def _reference_post_allowed(path: str, query: str) -> bool:
    """Independent re-statement of the POST allowlist written with plain string logic, not regexes (differential test)."""
    p = path.split("/")
    if p == ["", "providers", "Microsoft.ResourceGraph", "resources"] or (
        len(p) == 4 and p[:2] == ["", "providers"] and p[2].lower() == "microsoft.resourcegraph" and p[3].lower() == "resources"
    ):
        return True
    low = [x.lower() for x in p]
    n = len(low)
    scope_ok = False
    if n >= 3 and low[1] == "subscriptions" and low[2] and "/" not in p[2]:
        rest = 3
        if n >= 5 and low[3] == "resourcegroups" and p[4]:
            rest = 5
        scope_ok = True
    elif n >= 5 and low[1:3] == ["providers", "microsoft.management"] and low[3] == "managementgroups" and p[4]:
        rest = 5
        scope_ok = True
    if (
        scope_ok
        and low[rest : rest + 2] == ["providers", "microsoft.costmanagement"]
        and len(low) == rest + 3
        and low[rest + 2] in ("query", "forecast")
    ):
        import re

        return bool(re.search(r"(?:^|&)api-version=\d{4}-\d{2}-\d{2}(?:&|$)", query))
    return False


PATHS = st.one_of(
    st.just("/providers/Microsoft.ResourceGraph/resources"),
    st.builds(
        lambda s, t: f"/subscriptions/{s}/providers/Microsoft.CostManagement/{t}",
        st.text(string.ascii_lowercase + "-", min_size=1, max_size=6),
        st.sampled_from(["query", "forecast", "Query", "externalSubscriptions", "query/", "queryx", "exports"]),
    ),
    st.builds(
        lambda s, g, t: f"/subscriptions/{s}/resourceGroups/{g}/providers/Microsoft.CostManagement/{t}",
        st.text(string.ascii_lowercase, min_size=1, max_size=4),
        st.text(string.ascii_lowercase, min_size=1, max_size=4),
        st.sampled_from(["query", "forecast", "generateCostDetailsReport"]),
    ),
    st.builds(
        lambda s, t: f"/providers/Microsoft.Management/managementGroups/{s}/providers/Microsoft.CostManagement/{t}",
        st.text(string.ascii_lowercase, min_size=1, max_size=4),
        st.sampled_from(["query", "forecast", "dimensions"]),
    ),
    st.lists(SEG, min_size=1, max_size=7).map(lambda xs: "/" + "/".join(xs)),
)
QUERIES = st.sampled_from(
    [
        "",
        "api-version=2023-03-01",
        "api-version=2023-03-01-preview",
        "api-version=latest",
        "x=1&api-version=2021-10-01",
        "api-version=2021-10-01&x=1",
        "api-version=20230301",
    ]
)


@given(path=PATHS, query=QUERIES)
def test_post_allowlist_matches_an_independent_reference(path, query):
    c = http.Client(Tok(), Boom(), sleep=lambda s: None)
    url = f"{HOST}{path}" + (f"?{query}" if query else "")
    try:
        c._check("POST", url)
        allowed = True
    except BlockedRequest:
        allowed = False
    assert allowed == _reference_post_allowed(path, query), (path, query)


HOSTISH = st.sampled_from(
    [
        "https://management.azure.com",
        "https://management.azure.com.evil.example",
        "https://evil.example\\@management.azure.com",
        "https://evil.example#@management.azure.com",
        "https://management.azure.com@evil.example",
        "https://evil.example?@management.azure.com",
        "https://management.azure.com:443",
        "https://management.azure.com:80@evil.example",
        "http://management.azure.com",
        "https://MANAGEMENT.AZURE.COM",
        "https:/\\management.azure.com",
        "https://management.azure.com%2f@evil.example",
        "https://management.azure.com\t.evil.example",
    ]
)


@given(host=HOSTISH, tail=st.text(alphabet=string.ascii_letters + "/?#@\\.%:", max_size=12))
def test_host_the_check_approves_is_the_host_urllib_connects_to(host, tail):
    """Parser-differential guard: the allowlist reads the URL with urlparse; the transport sends it with urllib.request. They must agree."""
    url = host + "/subscriptions" + tail
    c = http.Client(Tok(), Boom(), sleep=lambda s: None)
    try:
        c._check("GET", url)
    except BlockedRequest:
        return
    try:
        real = urllib.request.Request(url).host
    except ValueError:
        return  # urllib itself refuses it
    assert real is not None and real.split(":")[0].lower() == "management.azure.com", (url, real)


# ---- 2. retry and paging ----------------------------------------------------------------------------------------------------------------
@given(statuses=st.lists(st.sampled_from([200, 429, 503, 404]), min_size=1, max_size=12), max_retries=st.integers(0, 6))
def test_retry_never_exceeds_its_budget_and_returns_the_deciding_response(statuses, max_retries):
    full = statuses + [200] * (max_retries + 2)  # padding so the script never runs dry
    t = Script(http.Response(s, {"retry-after": "0"}, {}) for s in full)
    sleeps = []
    c = http.Client(Tok(), t, sleep=sleeps.append, max_retries=max_retries)
    r = c.request("GET", HOST + "/subscriptions?api-version=2022-01-01")
    assert len(t.sent) <= max_retries + 1
    first_final = next(i for i, s in enumerate(full) if s not in (429, 503))
    if first_final <= max_retries:
        assert r.status == full[first_final] and len(t.sent) == first_final + 1
    else:
        assert len(t.sent) == max_retries + 1 and len(sleeps) == max_retries
    assert c.calls[-1].retries == len(sleeps)


@given(total=st.integers(0, 60), size=st.integers(1, 17))
def test_paging_returns_every_row_once_in_order(total, size):
    ids = [f"/r/{i:03d}" for i in range(total)]
    chunks = [ids[i : i + size] for i in range(0, total, size)] or [[]]
    resp = []
    for i, ch in enumerate(chunks):
        b = {"data": [{"id": x} for x in ch], "totalRecords": total, "resultTruncated": False}
        if i < len(chunks) - 1:
            b["$skipToken"] = f"t{i}"
        resp.append(http.Response(200, {}, b))
    c = http.Client(Tok(), Script(resp), sleep=lambda s: None)
    res = arg.query(c, "resources | project id | order by id asc", page_size=size)
    assert [r["id"] for r in res.rows] == ids and res.pages == len(chunks)


@given(total=st.integers(2, 40), got=st.integers(1, 39))
def test_a_short_last_page_without_skip_token_is_never_accepted_silently(total, got):
    assume(got < total)
    body = {"data": [{"id": str(i)} for i in range(got)], "totalRecords": total, "resultTruncated": False}
    c = http.Client(Tok(), Script([http.Response(200, {}, body)]), sleep=lambda s: None)
    with pytest.raises(arg.IncompleteResult):
        arg.query(c, "resources | project id | order by id asc")


# ---- 3. fingerprints, comparison, maturity, redaction -------------------------------------------------------------------------------------
DETAILS = st.dictionaries(
    st.text(string.ascii_lowercase, min_size=1, max_size=5),
    st.one_of(st.integers(), st.text(max_size=6), st.booleans(), st.none()),
    max_size=6,
)


@given(d=DETAILS, rid=st.text(string.ascii_lowercase + "/", min_size=1, max_size=12))
def test_fingerprint_ignores_key_order_and_changes_with_content(d, rid):
    f1 = Finding("ORPH-DISK-01", rid, "low", "m", dict(d))
    f2 = Finding("ORPH-DISK-01", rid, "low", "m", dict(reversed(list(d.items()))))
    assert fingerprint(f1) == fingerprint(f2)
    assert fingerprint(Finding("ORPH-DISK-01", rid + "x", "low", "m", dict(d))) != fingerprint(f1)


def _doc(findings):
    d = json.loads(json.dumps(GOLDEN))
    d["findings"] = findings
    return d


SUBSETS = st.lists(st.booleans(), min_size=len(GOLDEN["findings"]), max_size=len(GOLDEN["findings"]))


@given(a=SUBSETS, b=SUBSETS)
def test_compare_is_symmetric_and_accounts_for_every_finding(a, b):
    fa = [f for f, k in zip(GOLDEN["findings"], a, strict=True) if k]
    fb = [f for f, k in zip(GOLDEN["findings"], b, strict=True) if k]
    ab, ba = compare.compare(_doc(fa), _doc(fb)), compare.compare(_doc(fb), _doc(fa))
    assert ab["counts"]["new"] == ba["counts"]["no_longer_reported"] and ab["counts"]["no_longer_reported"] == ba["counts"]["new"]
    keys = {(f["check_id"], f["resource_id"]) for f in fa} | {(f["check_id"], f["resource_id"]) for f in fb}
    ran = {c["id"] for c in GOLDEN["manifest"]["checks"] if c["status"] == "ran"}
    assert len(ab["items"]) == len([k for k in keys if k[0] in ran])
    same = compare.compare(_doc(fa), _doc(fa))
    assert same["counts"]["new"] == same["counts"]["no_longer_reported"] == same["counts"]["worse"] == same["counts"]["changed"] == 0


ANS = st.dictionaries(st.integers(1, maturity.QUESTIONS).map(lambda i: f"q{i}"), st.sampled_from(list("ABCD")), max_size=maturity.QUESTIONS)


@given(ans=ANS, q=st.integers(1, maturity.QUESTIONS))
def test_maturity_counts_add_up_and_raising_one_answer_never_lowers_a_level(ans, q):
    r = maturity.evaluate({"answers": ans, "targets": {}})
    assert len(r["capabilities"]) == len(maturity.CAPABILITIES) and sum(r["counts"].values()) == len(maturity.CAPABILITIES)
    key = f"q{q}"
    cur = ans.get(key)
    order = "ABC"
    if cur is not None and cur in order and cur != "C":
        raised = dict(ans, **{key: order[order.index(cur) + 1]})
        r2 = maturity.evaluate({"answers": raised, "targets": {}})
        for x, y in zip(r["capabilities"], r2["capabilities"], strict=True):
            if x["current"] is not None:
                assert maturity.LEVELS.index(y["current"]) >= maturity.LEVELS.index(x["current"])


NAMES = st.text(string.ascii_lowercase + string.digits, min_size=6, max_size=10).map(lambda s: "zq" + s)


@given(
    sub=NAMES,
    rg=NAMES,
    res=NAMES,
    salt=st.text(string.hexdigits, min_size=4, max_size=8),
    salt2=st.text(string.hexdigits, min_size=4, max_size=8),
)
def test_redaction_hides_every_name_and_is_stable_within_a_salt(sub, rg, res, salt, salt2):
    assume(len({sub, rg, res}) == 3 and salt != salt2)
    rid = f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{res}"
    out = redact.resource_id(rid, salt)
    assert not any(n in out for n in (sub, rg, res))
    assert "Microsoft.Compute/virtualMachines" in out
    assert out == redact.resource_id(rid, salt)
    assert out != redact.resource_id(rid, salt2)
    assert math.isfinite(len(out))
