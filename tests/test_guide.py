"""`fcat guide`: scripted question-and-answer runs. Nothing is executed for real: the doctor and run calls are recorded."""

import datetime as dt

import pytest

from fcat import cli, config, guide

TODAY = dt.date(2026, 10, 21)


class Script:
    def __init__(self, *answers):
        self.answers, self.asked, self.said = list(answers), [], []

    def ask(self, prompt):
        self.asked.append(prompt)
        return self.answers.pop(0)

    def say(self, text=""):
        self.said.append(text)

    @property
    def text(self):
        return "\n".join(self.said)


class Calls:
    def __init__(self, *codes):
        self.codes, self.calls = list(codes), []

    def __call__(self, argv):
        self.calls.append(argv)
        return self.codes.pop(0)


def go(tmp_path, script, calls, az=True):
    return guide.run(script.ask, script.say, calls, (lambda n: "/usr/bin/az") if az else (lambda n: None), tmp_path, TODAY)


HAPPY = ["y", "Acme Ltd", "Contoso Cloud", "", "n", "n", "n", "n", "n", "n", "y"]


def test_happy_path_writes_config_runs_doctor_then_run(tmp_path):
    s, c = Script(*HAPPY), Calls(0, 0)
    assert go(tmp_path, s, c) == 0
    folder = tmp_path / "acme-ltd-2026-10-21"
    cfg = config.load(folder / "config.toml")
    assert cfg.subscriptions == [] and not cfg.governance_apis and not cfg.cost_apis and not cfg.rightsizing
    assert cfg.report.title == "Cloud cost review" and cfg.report.prepared_for == "Acme Ltd"
    assert [x[0] for x in c.calls] == ["doctor", "run"] and c.calls[1][-2:] == ["--out", str(folder / "output")]
    assert "dashboard-operator.html" in s.text and "purge" in s.text


def test_options_and_subscriptions_end_up_in_the_config(tmp_path):
    guid = "11111111-2222-3333-4444-555555555555"
    s = Script("y", "Acme", "Me", "T", "y", "not-an-id", guid, "y", "y", "n", "y", "n", "y")
    assert go(tmp_path, s, Calls(0, 0)) == 0
    cfg = config.load(tmp_path / "acme-2026-10-21" / "config.toml")
    assert cfg.subscriptions == [guid] and cfg.governance_apis and cfg.cost_apis and not cfg.rightsizing
    assert cfg.storage_apis is True and cfg.compute_apis is False
    assert "36 characters" in s.text


def test_stops_without_running_anything(tmp_path):
    c = Calls()
    assert go(tmp_path, Script("n"), c) == 1  # not signed in
    assert go(tmp_path, Script("y", "A", "B", "", "n", "n", "n", "n", "n", "n", "n"), c) == 1  # declines at the summary
    assert c.calls == [] and not list(tmp_path.iterdir())  # nothing written either


def test_missing_az_is_a_clear_stop(tmp_path):
    s = Script()
    assert go(tmp_path, s, Calls(), az=False) == 2 and "not installed" in s.text and s.asked == []


def test_failed_access_check_asks_before_continuing(tmp_path):
    s, c = Script(*HAPPY, "n"), Calls(1)
    assert go(tmp_path, s, c) == 1 and [x[0] for x in c.calls] == ["doctor"] and "did not pass" in s.text
    s, c = Script(*HAPPY, "y"), Calls(1, 0)
    assert go(tmp_path / "b", s, c) == 0 and [x[0] for x in c.calls] == ["doctor", "run"]


def test_failed_audit_and_run_error_are_reported_not_hidden(tmp_path):
    s = Script(*HAPPY)
    assert go(tmp_path, s, Calls(0, 3)) == 3 and "self-audit FAILED" in s.text and "dashboard-customer" not in s.text
    s = Script(*HAPPY)
    assert go(tmp_path / "b", s, Calls(0, 2)) == 2 and "stopped with an error" in s.text


def test_second_run_the_same_day_does_not_overwrite(tmp_path):
    assert go(tmp_path, Script(*HAPPY), Calls(0, 0)) == 0
    first = (tmp_path / "acme-ltd-2026-10-21" / "config.toml").read_text()
    assert go(tmp_path, Script(*HAPPY), Calls(0, 0)) == 0
    assert (tmp_path / "acme-ltd-2026-10-21-2" / "config.toml").is_file() and (
        tmp_path / "acme-ltd-2026-10-21" / "config.toml"
    ).read_text() == first


@pytest.mark.parametrize("name", ['Ac"me\\ Ltd', "Ünï ✓ <b>", "x" * 120])
def test_awkward_customer_names_survive_the_config_round_trip(tmp_path, name):
    s = Script("y", name, "Me", "T", "n", "n", "n", "n", "n", "n", "y")
    assert go(tmp_path, s, Calls(0, 0)) == 0
    cfg = config.load(next(tmp_path.glob("*/config.toml")))
    assert cfg.report.prepared_for == name


def test_toml_string_rejects_control_characters_and_slug_is_safe():
    with pytest.raises(ValueError):
        guide.toml_str("a\nb")
    assert guide.slug("../../Etc/Passwd & Co.") == "etc-passwd-co" and guide.slug("") == "customer" and len(guide.slug("a" * 99)) == 40


def test_text_question_refuses_control_characters_and_too_long_answers():
    s = Script("bad\x07", "x" * 500, "fine")
    assert guide._text(s.ask, "Q") == "fine"


def test_cli_guide_handles_ctrl_c(monkeypatch, capsys):
    def boom(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr(guide, "run", boom)
    assert cli.main(["guide"]) == 1 and "Nothing further was run" in capsys.readouterr().out
