"""Run configuration (TOML, stdlib tomllib). Toggles are set by the owner only."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field

PROFILES = {"quick": {"cheap_only": True}, "standard": {"cheap_only": False}, "deep": {"cheap_only": False}}


@dataclass
class Config:
    profile: str = "standard"
    domains: dict = field(default_factory=dict)  # domain -> bool
    checks: dict = field(default_factory=dict)  # check id -> bool
    subscriptions: list = field(default_factory=list)
    management_groups: list = field(default_factory=list)

    def as_dict(self):
        return {
            "profile": self.profile,
            "domains": self.domains,
            "checks": self.checks,
            "subscriptions_count": len(self.subscriptions),
            "management_groups_count": len(self.management_groups),
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
    return Config(prof, d.get("domains", {}), d.get("checks", {}), run.get("subscriptions", []), run.get("management_groups", []))
