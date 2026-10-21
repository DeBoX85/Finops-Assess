#!/usr/bin/env python3
"""Documentation consistency check. Prints warnings; exit 1 only on missing required files/sections."""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED = [
    "CLAUDE.md",
    "README.md",
    "NOTICE.md",
    "docs/HANDOVER.md",
    "docs/PLAN.md",
    "docs/DEV-PRINCIPLES.md",
    "docs/MISTAKES.md",
    "docs/REVERT.md",
    "docs/RESUME_PROMPT.md",
    "docs/CHECKPOINTS.md",
    "docs/QUALITY.md",
]
SECTIONS = ["## State", "## Done", "## In progress", "## Next step", "## Open questions", "## Blockers"]


def check():
    errs, warns = [], []
    for f in REQUIRED:
        if not (ROOT / f).exists():
            errs.append(f"missing required file: {f}")
    h = ROOT / "docs/HANDOVER.md"
    if h.exists():
        t = h.read_text()
        for s in SECTIONS:
            if s not in t:
                errs.append(f"HANDOVER.md missing section: {s}")
        if "<!-- auto:start -->" not in t or "<!-- auto:end -->" not in t:
            errs.append("HANDOVER.md missing auto block markers")
    nums = sorted(int(m.group(1)) for p in (ROOT / "docs/decisions").glob("*.md") if (m := re.match(r"(\d{4})-", p.name)))
    if nums and nums != list(range(nums[0], nums[0] + len(nums))):
        warns.append(f"decision record numbering has gaps: {nums}")
    # Relative links in every markdown file under docs/ (recursive) plus the root files. Broken links are errors.
    # Not checked: anchors (#...), absolute URLs (no network), and links inside fenced code blocks.
    for p in [*(ROOT / "docs").rglob("*.md"), ROOT / "README.md", ROOT / "NOTICE.md", ROOT / "CLAUDE.md"]:
        if not p.exists():
            continue
        text = re.sub(r"```.*?```", "", p.read_text(), flags=re.S)
        for m in re.finditer(r"\]\((?!https?:|#|mailto:)([^)\s]+)\)", text):
            target = m.group(1).split("#")[0]
            if target and not (p.parent / target).exists():
                errs.append(f"{p.relative_to(ROOT)}: broken relative link {m.group(1)}")
    return errs, warns


if __name__ == "__main__":
    e, w = check()
    for x in e:
        print("ERROR:", x)
    for x in w:
        print("WARN:", x)
    print("docs check:", "FAIL" if e else "ok", f"({len(w)} warnings)")
    sys.exit(1 if e else 0)
