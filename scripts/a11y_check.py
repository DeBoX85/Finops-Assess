#!/usr/bin/env python3
"""Accessibility check of both dashboards with axe-core in headless Chromium (development gate, never part of a customer run).
Renders the golden synthetic report for both audiences with the Changes and Maturity sections, opens every view in light and dark,
and runs axe-core rules for WCAG 2.0 to 2.2 A and AA plus best practice. Exit 0 = no violations, 1 = violations, 2 = could not run.
axe-core 4.10.2 (MPL-2.0) is downloaded from npm into the ignored .cache folder; nothing from it is copied into the repo.
Limit (axe-core's own README, read 2026-10-21): automated rules find on average about 57% of WCAG issues; manual review is still needed."""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
AXE_VERSION = "4.10.2"
AXE_DIR = ROOT / ".cache" / "axe"
AXE_JS = AXE_DIR / "node_modules" / "axe-core" / "axe.min.js"
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]


def ensure_axe() -> str | None:
    """Returns None when axe is ready, otherwise the reason it is not."""
    if AXE_JS.is_file():
        return None
    npm = shutil.which("npm")
    if not npm:
        return "npm is not installed, so axe-core cannot be fetched"
    AXE_DIR.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([npm, "install", "--silent", "--prefix", str(AXE_DIR), f"axe-core@{AXE_VERSION}"], capture_output=True, text=True)  # noqa: S603
    return None if AXE_JS.is_file() else f"npm install of axe-core failed: {r.stderr.strip()[-200:]}"


def build_pages(out: pathlib.Path) -> dict[str, pathlib.Path]:
    from fcat import compare, dash, maturity

    golden = json.loads((ROOT / "tests" / "golden" / "report.json").read_text())
    older = json.loads(json.dumps(golden))
    older["findings"] = older["findings"][1:]  # one finding "new" in the newer run, so the Changes section has content
    ch = compare.compare(older, golden)
    for i in ch["items"]:
        i["name"] = i["resource_id"].rstrip("/").rsplit("/", 1)[-1]
    ch["items"] = [i for i in ch["items"] if i["state"] != "unchanged"]
    mat = maturity.evaluate(maturity.load(ROOT / "tests" / "fixtures" / "maturity_sample.toml"))
    pages = {}
    for aud in ("operator", "customer"):
        p = out / f"{aud}.html"
        dash.render(p, golden, aud, None, ch, mat)
        pages[aud] = p
    return pages


def run() -> tuple[int, list[str]]:
    why = ensure_axe()
    if why:
        return 2, [f"not run, because {why}"]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return 2, ["not run, because playwright is not installed"]
    axe = AXE_JS.read_text()
    lines: list[str] = []
    bad = 0
    with tempfile.TemporaryDirectory() as t, sync_playwright() as pw:
        pages = build_pages(pathlib.Path(t))
        try:
            browser = pw.chromium.launch()
        except Exception as e:  # noqa: BLE001  a missing browser is "not run", never a pass
            return 2, [f"not run, because Chromium could not start: {type(e).__name__}"]
        for aud, path in pages.items():
            for scheme in ("light", "dark"):
                pg = browser.new_context(color_scheme=scheme, viewport={"width": 1280, "height": 900}).new_page()
                pg.goto(path.as_uri())
                views = [v.strip() for v in pg.locator("nav[aria-label=Sections] button").all_inner_texts()]
                if len(views) < 5:
                    lines.append(f"{aud}/{scheme}: only {len(views)} views found, expected at least 5")
                    bad += 1
                for v in views:
                    pg.locator("nav[aria-label=Sections] button", has_text=v).first.click()
                    pg.evaluate(axe)
                    res = pg.evaluate(
                        "tags => axe.run(document,{runOnly:{type:'tag',values:tags}}).then(r=>r.violations.map(v=>({id:v.id,impact:v.impact,n:v.nodes.length,help:v.help})))",
                        TAGS,
                    )
                    for x in res:
                        bad += 1
                        lines.append(f"{aud}/{scheme}/{v}: {x['id']} ({x['impact']}, {x['n']} nodes): {x['help']}")
        browser.close()
    return (1 if bad else 0), lines or ["no axe violations in 2 audiences x 2 colour schemes x every view"]


if __name__ == "__main__":
    code, msgs = run()
    print("\n".join(msgs))
    sys.exit(code)
