"""Browser-level checks of the dashboards in headless Chromium (skipped when Chromium or Playwright is missing; a skip is reported by the gates as 'not run').
Covers what string tests cannot: no network requests, no script errors, no horizontal overflow on phones, and a budget for large estates."""

import json
import pathlib
import sys
import time

import pytest

pw_sync = pytest.importorskip("playwright.sync_api")

from fcat import compare, dash, maturity  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = json.loads((ROOT / "tests" / "golden" / "report.json").read_text())
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="module")
def browser():
    with pw_sync.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"Chromium could not start: {type(e).__name__}")
        yield b
        b.close()


def _pages(tmp_path, doc=GOLDEN):
    older = json.loads(json.dumps(doc))
    older["findings"] = older["findings"][1:]
    ch = compare.compare(older, doc)
    for i in ch["items"]:
        i["name"] = i["resource_id"].rsplit("/", 1)[-1]
    mat = maturity.evaluate(maturity.load(ROOT / "tests" / "fixtures" / "maturity_sample.toml"))
    out = {}
    for aud in ("operator", "customer"):
        p = tmp_path / f"{aud}.html"
        dash.render(p, doc, aud, None, ch, mat)
        out[aud] = p
    return out


@pytest.mark.parametrize("aud", ["operator", "customer"])
@pytest.mark.parametrize("width", [1280, 390])
def test_every_view_has_no_errors_no_requests_no_overflow(browser, tmp_path, aud, width):
    page_path = _pages(tmp_path)[aud]
    pg = browser.new_page(viewport={"width": width, "height": 900})
    errors, requests = [], []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.on("request", lambda r: requests.append(r.url) if not r.url.startswith(("file:", "data:")) else None)
    pg.goto(page_path.as_uri())
    views = [v.strip() for v in pg.locator("nav[aria-label=Sections] button").all_inner_texts()]
    assert len(views) >= 5, views
    for v in views:
        pg.locator("nav[aria-label=Sections] button", has_text=v).first.click()
        assert not pg.evaluate("document.documentElement.scrollWidth > innerWidth"), f"{aud} {width}px overflow in {v}"
    assert errors == [] and requests == []


def test_print_layout_has_no_overflow_and_shows_every_view(browser, tmp_path):
    pg = browser.new_page(viewport={"width": 794, "height": 1123})
    pg.goto(_pages(tmp_path)["customer"].as_uri())
    pg.emulate_media(media="print")
    assert not pg.evaluate("document.documentElement.scrollWidth > innerWidth")
    shown = pg.evaluate("[...document.querySelectorAll('.view')].filter(v=>getComputedStyle(v).display!=='none').length")
    assert shown >= 5
    assert pg.evaluate("getComputedStyle(document.querySelector('.cover')).display") == "block"


def test_large_estate_stays_within_budget(browser, tmp_path):
    """10,000 findings: file under 8 MB, first paint under 5 s, Findings view under 3 s (measured: 4.2 MB, 0.5 s, 0.2 s; budgets are ~10x)."""
    doc = json.loads(json.dumps(GOLDEN))
    base = doc["findings"]
    fs = []
    for i in range(10_000):
        f = json.loads(json.dumps(base[i % len(base)]))
        f["resource_id"] += f"-x{i}"
        f["fingerprint"] = f"{i:016x}"
        fs.append(f)
    doc["findings"] = fs
    p = tmp_path / "big.html"
    dash.render(p, doc, "customer")
    assert p.stat().st_size < 8_000_000
    pg = browser.new_page()
    t0 = time.time()
    pg.goto(p.as_uri())
    pg.wait_for_selector("nav")
    assert time.time() - t0 < 5
    t1 = time.time()
    pg.locator("nav[aria-label=Sections] button", has_text="Findings").click()
    assert time.time() - t1 < 3
