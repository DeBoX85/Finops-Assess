import gzip

import pytest

from fcat import cli, focus_import
from fcat.errors import FcatError

HDR = "BilledCost,EffectiveCost,ListCost,BillingCurrency,ChargePeriodStart,ServiceName,SubAccountId,ResourceId\n"


def write(tmp_path, body, name="a.csv"):
    p = tmp_path / name
    p.write_text(HDR + body)
    return p


def test_aggregates(tmp_path):
    p = write(
        tmp_path,
        "1.5,1.2,2,EUR,2026-09-01T00:00:00Z,VMs,s1,r1\n2,2,3,EUR,2026-09-02T00:00:00Z,VMs,s1,r2\n1,1,1,EUR,2026-09-02T00:00:00Z,Storage,s2,r3\n",
    )
    d = focus_import.import_files([p])
    assert d["rows"] == 3 and d["currency"] == "EUR"
    assert d["totals"]["BilledCost"] == 4.5
    assert d["by_service"]["VMs"]["ListCost"] == 5
    assert d["period"] == {"first_day": "2026-09-01", "last_day": "2026-09-02"}


def test_gz_and_folder(tmp_path):
    (tmp_path / "x.csv.gz").write_bytes(gzip.compress((HDR + "1,1,1,EUR,2026-09-01T00:00Z,A,s,r\n").encode()))
    assert focus_import.import_files([tmp_path])["rows"] == 1


def test_mixed_currency_refused(tmp_path):
    p = write(tmp_path, "1,1,1,EUR,2026-09-01,A,s,r\n1,1,1,USD,2026-09-01,A,s,r\n")
    with pytest.raises(FcatError, match="mixed"):
        focus_import.import_files([p])


def test_not_focus_file(tmp_path):
    p = tmp_path / "b.csv"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(FcatError, match="missing required"):
        focus_import.import_files([p])


def test_missing_optional_cost_column_reported(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text("BilledCost,BillingCurrency,ChargePeriodStart,ServiceName,SubAccountId\n1,EUR,2026-09-01,A,s\n")
    d = focus_import.import_files([p])
    assert "ListCost" in d["columns_missing"] and "ListCost" not in d["totals"]


def test_bad_rows_counted_not_hidden(tmp_path):
    p = write(tmp_path, "x,1,1,EUR,2026-09-01,A,s,r\n1,1,1,EUR,2026-09-01,A,s,r\n")
    d = focus_import.import_files([p])
    assert d["unparseable_rows"] == 1 and d["rows"] == 1


def test_cli(tmp_path):
    p = write(tmp_path, "1,1,1,EUR,2026-09-01,A,s,r\n")
    assert cli.main(["import-focus", str(p), "--out", str(tmp_path / "o")]) == 0
    assert (tmp_path / "o/snapshot/cost_focus.json").exists()
