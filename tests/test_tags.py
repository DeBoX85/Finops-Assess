"""Phase 1 cost governance: properties of tags.py and the TAG/POL checks that the generic accuracy tests skip (estate-level checks)."""

import copy
import json
import pathlib
import random
from collections import Counter

from fcat import arg, checks, redact, tags
from tests.test_core import client, page

checks.load_builtin()
FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "checks"


def _case(check_id, name_part):
    for c in json.loads((FIX / f"{check_id}.json").read_text())["cases"]:
        if name_part in c["name"]:
            return c
    raise AssertionError(name_part)


def _inv(rows):
    return tags.inventory(rows)


def _rows(n, tg, sub="s1"):
    return [
        {"id": f"/subscriptions/{sub}/resourceGroups/rg/providers/x/y/r{i}", "type": "x/y", "subscriptionId": sub, "tags": tg}
        for i in range(n)
    ]


def test_inventory_is_order_independent():
    rows = _rows(6, {"Env": "a"}) + _rows(4, None) + _rows(3, {"env": "b", "owner": "o"})
    shuffled = rows[:]
    random.Random(1).shuffle(shuffled)
    a, b = _inv(rows), _inv(shuffled)
    assert a["total"] == b["total"] == 13 and a["tagged"] == b["tagged"] == 9
    assert a["keys"]["env"]["resources"] == b["keys"]["env"]["resources"] == 9
    assert a["keys"]["env"]["casings"] == Counter({"Env": 6, "env": 3})


def test_relabelling_key_casing_does_not_change_coverage():
    rows = _rows(8, {"env": "p"}) + _rows(4, None)
    up = copy.deepcopy(rows)
    for r in up:
        if r["tags"]:
            r["tags"] = {"ENV": "p"}
    assert tags.scheme(_inv(rows), [])["keys"] == tags.scheme(_inv(up), [])["keys"] == ["env"]
    assert _inv(rows)["keys"]["env"]["resources"] == _inv(up)["keys"]["env"]["resources"]


def test_scheme_precedence_policy_then_inferred_then_none():
    inv = _inv(_rows(10, {"owner": "x"}))
    pol = [{"tag": "CostCenter"}]
    assert tags.scheme(inv, pol)["source"] == "policy" and tags.scheme(inv, pol)["keys"] == ["costcenter"]
    assert tags.scheme(inv, [])["source"] == "inferred" and tags.scheme(inv, [])["keys"] == ["owner"]
    assert tags.scheme(_inv(_rows(10, None)), [])["source"] == "none"
    assert tags.scheme(_inv([]), [])["source"] == "none"  # empty estate: no division by zero


def test_bad_tag_shapes_count_as_untagged():
    for bad in (None, [], "x", 5, {"k": None}):
        assert isinstance(tags.tags_of({"tags": bad}), dict)
    assert tags.tags_of({"tags": {"k": None}}) == {"k": ""}


def test_value_variants_fold_case_space_and_separators_but_not_synonyms():
    v = Counter({"Prod": 3, "prod ": 2, "PROD": 1, "production": 9, "pre_prod": 1, "pre-prod": 1})
    groups = tags.value_variants(v)
    flat = [{x["value"] for x in g} for g in groups]
    assert {"Prod", "prod ", "PROD"} in flat and {"pre_prod", "pre-prod"} in flat
    assert not any("production" in g for g in flat)


def test_classify_assignment():
    base = "/providers/Microsoft.Authorization/policyDefinitions/871b6d14-10aa-478d-b590-94f262ecfa99"
    c = tags.classify_assignment(
        {"id": "a", "definitionId": base, "parameters": {"tagName": {"value": "env"}}, "enforcementMode": "DoNotEnforce"}
    )
    assert c["kind"] == "require" and c["tag"] == "env" and c["enforced"] is False
    assert (
        tags.classify_assignment({"definitionId": base.replace("policyDefinitions", "policySetDefinitions")}) is None
    )  # initiative: not guessed
    assert tags.classify_assignment({"definitionId": "/providers/x/policyDefinitions/00000000-0000-0000-0000-000000000000"}) is None
    assert tags.classify_assignment(None) is None
    assert tags.classify_assignment({"definitionId": base, "parameters": None})["tag"] is None  # unreadable name is never invented


def test_redact_masks_tag_values_but_not_keys_or_counts():
    f = checks.Finding(
        "TAG-VAL-01", "tag:env", "low", "m", {"key": "env", "variants": [[{"value": "Prod", "count": 3}, {"value": "prod", "count": 1}]]}
    )
    (g,) = redact.findings([f], "salt")
    flat = json.dumps(g.details)
    assert "Prod" not in flat and "prod" not in flat.replace("val-", "")  # values gone
    vals = [x["value"] for grp in g.details["variants"] for x in grp]
    assert all(v.startswith("val-") for v in vals) and vals[0] != vals[1]
    assert [x["count"] for x in g.details["variants"][0]] == [3, 1] and g.details["key"] == "env"


def test_arg_query_sends_authorization_scope_filter_only_when_asked():
    c, f, _ = client(page([], 0), page([], 0))
    arg.query(c, "policyresources | project id | order by id asc", authorization_scope_filter="AtScopeAboveAndBelow")
    arg.query(c, "resources | project id | order by id asc")
    assert f.sent[0][2]["options"]["authorizationScopeFilter"] == "AtScopeAboveAndBelow"
    assert "authorizationScopeFilter" not in f.sent[1][2]["options"]


def test_policy_collector_uses_the_scope_option():
    from fcat import collectors

    assert collectors.COLLECTOR_OPTIONS["policy_assignments"] == {"authorization_scope_filter": "AtScopeAboveAndBelow"}
