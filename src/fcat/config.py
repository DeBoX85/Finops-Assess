"""Run configuration (TOML, stdlib tomllib). Toggles are set by the owner only."""

from __future__ import annotations

import base64
import hashlib
import pathlib
import re
import tomllib
from dataclasses import dataclass, field

PROFILES = {"quick": {"cheap_only": True}, "standard": {"cheap_only": False}, "deep": {"cheap_only": False}}


HIDEABLE_SECTIONS = ("coverage", "collector_errors", "audit_detail")  # findings and the audit result line can never be hidden
MAX_LOGO_BYTES = 262144
TEXT_LIMITS = {"title": 120, "subtitle": 200, "prepared_by": 120, "prepared_for": 120, "footer": 400}


class ReportOptionsError(ValueError):
    pass


@dataclass
class ReportOptions:
    """Presentation only (docs/TAILORING.md). Never changes which checks run or what the JSON holds."""

    title: str = "F-CAT assessment report"
    subtitle: str = ""
    prepared_by: str = ""
    prepared_for: str = ""
    footer: str = ""
    accent: str = ""  # #RRGGBB or empty for the default palette
    logo_data_uri: str = ""
    logo_sha256: str = ""
    hide: tuple = ()

    def manifest_view(self) -> dict:
        """What the manifest records, so the reader can see how the report was tailored. No paths, no logo bytes."""
        return {
            "title": self.title,
            "prepared_by": bool(self.prepared_by),
            "prepared_for": bool(self.prepared_for),
            "accent": self.accent or None,
            "logo_sha256": self.logo_sha256 or None,
            "hidden_sections": list(self.hide),
        }


def parse_report_options(d: dict, base_dir=".") -> ReportOptions:
    if not isinstance(d, dict):
        raise ReportOptionsError("[report] must be a table")
    known = set(TEXT_LIMITS) | {"accent", "logo", "hide"}
    extra = set(d) - known
    if extra:
        raise ReportOptionsError(f"unknown [report] keys: {sorted(extra)}")
    o = ReportOptions()
    for k, lim in TEXT_LIMITS.items():
        if k in d:
            v = d[k]
            if not isinstance(v, str) or len(v) > lim or any(ord(c) < 32 for c in v):
                raise ReportOptionsError(f"[report] {k} must be text of at most {lim} characters without control characters")
            setattr(o, k, v)
    if "accent" in d:
        if not isinstance(d["accent"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", d["accent"]):
            raise ReportOptionsError("[report] accent must look like #1a7f37")
        o.accent = d["accent"]
    if "hide" in d:
        h = d["hide"]
        if not isinstance(h, list) or any(x not in HIDEABLE_SECTIONS for x in h):
            raise ReportOptionsError(
                f"[report] hide may only contain {list(HIDEABLE_SECTIONS)}; findings and the audit result cannot be hidden"
            )
        o.hide = tuple(sorted(set(h)))
    if "logo" in d:
        p = pathlib.Path(base_dir) / str(d["logo"])
        raw = p.read_bytes() if p.is_file() else None
        if raw is None or len(raw) > MAX_LOGO_BYTES:
            raise ReportOptionsError(f"[report] logo must be an existing file of at most {MAX_LOGO_BYTES} bytes")
        if raw.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"
        elif raw.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        elif p.suffix.lower() == ".svg" and raw.lstrip()[:1] == b"<":
            mime = "image/svg+xml"  # shown through <img>, where browsers do not run scripts inside SVG
        else:
            raise ReportOptionsError("[report] logo must be a PNG, JPEG or SVG file")
        o.logo_data_uri = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
        o.logo_sha256 = hashlib.sha256(raw).hexdigest()[:12]
    return o


def load_report_options(path) -> ReportOptions:
    """Per-run branding file: a TOML file with only a [report] table (for example for an external collaborator)."""
    with open(path, "rb") as f:
        d = tomllib.load(f)
    if set(d) - {"report"}:
        raise ReportOptionsError("a branding file may contain only a [report] table")
    return parse_report_options(d.get("report", {}), pathlib.Path(path).parent)


@dataclass
class Config:
    profile: str = "standard"
    domains: dict = field(default_factory=dict)  # domain -> bool
    checks: dict = field(default_factory=dict)  # check id -> bool
    subscriptions: list = field(default_factory=list)
    management_groups: list = field(default_factory=list)
    report: ReportOptions = field(default_factory=ReportOptions)
    rightsizing: bool = False  # opt-in: reads Azure Monitor metrics and compute SKUs (many GET calls); see docs/RIGHTSIZING.md
    rightsizing_max_vms: int = 50
    governance_apis: bool = False  # opt-in: 3 GET calls per subscription (budgets, anomaly rules, exports); see docs/COST-GOVERNANCE.md
    cost_apis: bool = False  # opt-in: one Cost Management Query per subscription plus a full resource id list; see docs/COST-DATA.md

    def as_dict(self):
        return {
            "profile": self.profile,
            "domains": self.domains,
            "checks": self.checks,
            "subscriptions_count": len(self.subscriptions),
            "management_groups_count": len(self.management_groups),
            "rightsizing": self.rightsizing,
            "rightsizing_max_vms": self.rightsizing_max_vms,
            "governance_apis": self.governance_apis,
            "cost_apis": self.cost_apis,
        }

    def enabled(self, meta) -> tuple[bool, str]:
        if self.checks.get(meta.id) is False:
            return False, "disabled by check toggle"
        if self.domains.get(meta.domain) is False:
            return False, "disabled by domain toggle"
        if PROFILES.get(self.profile, {}).get("cheap_only") and meta.run_cost != "low":
            return False, f"profile '{self.profile}' excludes run cost '{meta.run_cost}'"
        return True, ""


def load(path) -> Config:
    with open(path, "rb") as f:
        d = tomllib.load(f)
    run = d.get("run", {})
    prof = run.get("profile", "standard")
    if prof not in PROFILES:
        raise ValueError(f"unknown profile {prof!r}; expected one of {sorted(PROFILES)}")
    rep = parse_report_options(d.get("report", {}), pathlib.Path(path).parent)
    rs, cap = run.get("rightsizing", False), run.get("rightsizing_max_vms", 50)
    if not isinstance(rs, bool) or not isinstance(cap, int) or isinstance(cap, bool) or not 1 <= cap <= 500:
        raise ValueError("[run] rightsizing must be true or false and rightsizing_max_vms an integer from 1 to 500")
    gov = run.get("governance_apis", False)
    if not isinstance(gov, bool):
        raise ValueError("[run] governance_apis must be true or false")
    cost = run.get("cost_apis", False)
    if not isinstance(cost, bool):
        raise ValueError("[run] cost_apis must be true or false")
    return Config(
        prof,
        d.get("domains", {}),
        d.get("checks", {}),
        run.get("subscriptions", []),
        run.get("management_groups", []),
        rep,
        rs,
        cap,
        gov,
        cost,
    )
