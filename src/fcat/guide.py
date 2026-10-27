"""`fcat guide`: a question-and-answer front end for operators who are not comfortable with the command line (backlog 43).
It asks plain questions, writes a config file, checks access with the same probes as `fcat doctor`, and runs the normal read-only analysis.
It adds NO new capability: every step is a call to the same code the commands use, and nothing is written to Azure. It never signs in for you:
`az login` stays a deliberate human step with the identity the customer gave you. All input and output go through two functions so tests can drive it."""

from __future__ import annotations

import datetime as dt
import pathlib
import re
import shutil

from . import config as cfgmod

GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
OPTIONS = (
    ("governance_apis", "Read budgets, anomaly alert rules and cost exports (a few extra read calls per subscription)?"),
    ("cost_apis", "Read last month's cost per resource and compare it with the resource list (needs Cost Management Reader)?"),
    ("rightsizing", "Read Azure Monitor CPU metrics to look for oversized VMs (many read calls, slower)?"),
    ("storage_apis", "Read the lifecycle policy of each storage account (one read call per account)?"),
    (
        "compute_apis",
        "Read the VM size list to count vCPUs for the Hybrid Benefit checks (one read call per subscription and region with Windows VMs)?",
    ),
)


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:40] or "customer"


def toml_str(value: str) -> str:
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("control characters are not allowed")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_config(answers: dict) -> str:
    lines = ["[run]", 'profile = "standard"']
    if answers["subscriptions"]:
        lines.append("subscriptions = [" + ", ".join(toml_str(s) for s in answers["subscriptions"]) + "]")
    for key, _ in OPTIONS:
        if answers["options"].get(key):
            lines.append(f"{key} = true")
    lines += ["", "[report]"]
    for key in ("title", "prepared_for", "prepared_by"):
        if answers.get(key):
            lines.append(f"{key} = {toml_str(answers[key])}")
    return "\n".join(lines) + "\n"


def _yes(ask, prompt, default=False) -> bool:
    while True:
        a = ask(f"{prompt} [{'Y/n' if default else 'y/N'}] ").strip().lower()
        if not a:
            return default
        if a in ("y", "yes"):
            return True
        if a in ("n", "no"):
            return False


def _text(ask, prompt, default="", limit=120) -> str:
    while True:
        a = ask(f"{prompt}{f' [{default}]' if default else ''}: ").strip() or default
        if len(a) <= limit and not any(ord(c) < 32 for c in a):
            return a


def _subscriptions(ask, say) -> list:
    if not _yes(ask, "Limit the run to specific subscriptions? (No means everything the signed-in identity can read)"):
        return []
    while True:
        raw = ask("Subscription IDs, separated by commas: ")
        ids = [x.strip() for x in raw.split(",") if x.strip()]
        bad = [x for x in ids if not GUID.match(x)]
        if ids and not bad:
            return ids
        say(
            "Each subscription ID is 36 characters: hexadecimal digits in groups of 8, 4, 4, 4 and 12, separated by hyphens."
            if ids
            else "Enter at least one ID."
        )


def run(ask=input, say=print, main=None, which=shutil.which, base_dir=None, today=None) -> int:
    """Returns 0 when the analysis ran and the self-audit passed, 1 when the operator stopped, 2 for a problem, 3 when the self-audit failed."""
    from . import cli  # noqa: PLC0415

    main = main or cli.main
    say("F-CAT guided run. This tool only READS from Azure. It changes nothing in the customer's environment.")
    say("You can stop at any question with Ctrl+C. Nothing is run until you confirm at the end.\n")
    if not which("az"):
        say(
            "The Azure CLI (az) is not installed or not on the PATH. Install it, run `az login` with the identity the customer gave you, then start again."
        )
        return 2
    say("Step 1. Sign in. Run `az login` yourself with the identity the customer gave you, in this or another window.")
    if not _yes(ask, "Have you signed in with that identity?"):
        say("Sign in first, then start again. Nothing was run.")
        return 1
    say("\nStep 2. About the report.")
    answers: dict = {
        "prepared_for": _text(ask, "Customer name"),
        "prepared_by": _text(ask, "Prepared by (your company)"),
    }
    answers["title"] = _text(ask, "Report title", "Cloud cost review")
    say("\nStep 3. Scope.")
    answers["subscriptions"] = _subscriptions(ask, say)
    say("\nStep 4. Optional extra reads. Leave these off unless the owner told you to switch one on.")
    answers["options"] = {key: _yes(ask, q) for key, q in OPTIONS}
    now = today or dt.date.today()
    root = pathlib.Path(base_dir) if base_dir else pathlib.Path.home() / "fcat-runs"
    name = f"{slug(answers['prepared_for'])}-{now.isoformat()}"
    folder = root / name
    n = 2
    while folder.exists():
        folder = root / f"{name}-{n}"
        n += 1
    say("\nSummary")
    say(f"  Customer: {answers['prepared_for'] or '(not given)'}; prepared by: {answers['prepared_by'] or '(not given)'}")
    say(
        f"  Scope: {len(answers['subscriptions'])} subscription(s)"
        if answers["subscriptions"]
        else "  Scope: everything the identity can read"
    )
    say("  Extra reads: " + (", ".join(k for k, v in answers["options"].items() if v) or "none"))
    say(f"  Files will be written to: {folder}")
    if not _yes(ask, "Check access and run the analysis now?"):
        say("Stopped. Nothing was run and nothing was written.")
        return 1
    folder.mkdir(parents=True)
    cfg_path = folder / "config.toml"
    try:
        cfg_path.write_text(build_config(answers))
        cfgmod.load(cfg_path)
    except (ValueError, OSError) as e:
        say(f"The settings could not be saved: {e}")
        return 2
    out = folder / "output"
    say("\nChecking access (read-only probes)...")
    code = main(["doctor", "--config", str(cfg_path), "--out", str(out)])
    if code != 0:
        say("\nSome access checks did not pass. Read the table above. A missing permission means some checks will say 'not assessed'.")
        if not _yes(ask, "Continue with the analysis anyway?"):
            say(f"Stopped. Settings are saved in {cfg_path}.")
            return 1
    say("\nRunning the analysis. This can take several minutes...")
    code = main(["run", "--config", str(cfg_path), "--out", str(out)])
    if code == 3:
        say("\nThe self-audit FAILED. Do not use or hand over this report. Tell the owner.")
        return 3
    if code != 0:
        say(f"\nThe run stopped with an error (code {code}). Read the message above, then ask the owner.")
        return 2
    say(f"\nDone. Open {out / 'dashboard-operator.html'} in your browser (operator view, for you).")
    say(
        f"The customer version is {out / 'dashboard-customer.html'}. Read docs/OPERATOR-GUIDE.md, section 'Handing over', before sending anything."
    )
    say("When you are finished with the data: `fcat purge --out <the output folder>` (add --yes to delete).")
    return 0
