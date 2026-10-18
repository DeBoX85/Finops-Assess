import pytest

from fcat import billing


@pytest.mark.parametrize(
    "qid,expected",
    [
        ("EnterpriseAgreement_2014-09-01", "supported"),
        ("MSDNDevTest_2014-09-01", "supported"),
        ("Pay-as-you-go_2014-09-01", "supported"),
        ("CSP_2015-05-01", "depends"),
        ("CSP_MG_2017-12-01", "depends"),
        ("Sponsored_2016-01-01", "unsupported"),
        ("AzureForStudents_2018-01-01", "unsupported"),
        ("Default_2014-09-01", "unsupported"),
        ("  enterpriseagreement_2014-09-01 ", "supported"),
        ("Something_New", "unknown"),
        ("", "unknown"),
        (None, "unknown"),
    ],
)
def test_classify(qid, expected):
    assert billing.classify(qid)["cost_management"] == expected


def test_unknown_is_never_guessed_as_supported():
    assert billing.classify("PayAsYouGo-typo")["cost_management"] == "unknown"
