"""Optional offline browser smoke test for a checkout or an extracted archive.

Install Playwright and its Chromium browser separately. This script is not
required to build the portal or run the standard-library unit tests.
"""
import argparse
import csv
from pathlib import Path
from struct import unpack
from tempfile import TemporaryDirectory

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def png_size(path):
    header = path.read_bytes()[:24]
    assert header.startswith(b"\x89PNG\r\n\x1a\n"), path
    return unpack(">II", header[16:24])


def capture(page, folder, name):
    page.screenshot(path=folder / f"{name}.png")


def check_desktop(browser, home, directory):
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    errors, remote = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda req: remote.append(req.url) if req.url.startswith(("http:", "https:")) else None)
    page.goto(home)
    expect(page.get_by_role("heading", name="Evidence timeline")).to_be_visible()
    total = page.evaluate("window.observatoryData.timeline.length")
    expect(page.locator("#timeline-count")).to_have_text(f"{total} records")
    capture(page, directory, "desktop-home")

    page.locator(".featured-row").get_by_role("link", name="Reinstatement").click()
    record = page.locator('[data-record-id="EV-014"]')
    expect(record).to_have_attribute("open", "")
    expect(record.get_by_text("Nov 22, 2026", exact=True)).to_be_visible()
    expect(record.get_by_text("Nov 23, 2026", exact=True)).to_be_visible()
    assert "000104581026000090" in record.locator(".source-list li a").first.get_attribute("href")
    page.reload()
    expect(record).to_have_attribute("open", "")
    record.locator("summary").focus()
    page.keyboard.press("Enter")
    expect(record).not_to_have_attribute("open", "")
    page.keyboard.press("Enter")
    expect(record).to_have_attribute("open", "")

    page.get_by_label("Category", exact=True).select_option("governance")
    page.get_by_label("Find records", exact=True).fill("0001045810-26-000090")
    expect(page.locator("#timeline-count")).not_to_have_text("0 records")
    with page.expect_download() as item:
        page.get_by_role("button", name="Download filtered CSV").click()
    exported = directory / "filtered-test.csv"
    item.value.save_as(exported)
    with exported.open(newline="", encoding="utf-8") as source:
        subset = list(csv.DictReader(source))
    assert subset and all(row["category"] == "governance" for row in subset)
    assert "EV-014" in {row["id"] for row in subset}
    page.get_by_label("Find records", exact=True).fill("A phrase absent from the recording")
    expect(page.get_by_text("No records match these filters.")).to_be_visible()
    expect(page.get_by_role("button", name="Download filtered CSV")).to_be_disabled()
    page.get_by_role("button", name="Clear filters").click()
    expect(page.locator("#timeline-count")).to_have_text(f"{total} records")

    page.get_by_role("link", name="Financials", exact=True).click()
    expect(page.locator("#financial-table tr")).to_have_count(page.evaluate("window.observatoryData.financials.length"))
    page.get_by_label("Inspect quarter").select_option("FY2027-Q3")
    expect(page.locator("#metric-revenue")).to_have_text("$115.84B")
    expect(page.locator("#metric-share")).to_have_text("92.89%")
    expect(page.locator("#metric-rd")).to_have_text("6.43%")
    with page.expect_download() as item:
        page.get_by_role("button", name="Download trend charts as PNG").click()
    trend = directory / "quarterly-figure.png"
    item.value.save_as(trend)
    assert png_size(trend) == (1440, 640)
    page.get_by_label("Display period").select_option("recent")
    expect(page.locator("#financial-table tr")).to_have_count(8)
    chart = page.locator("#chart-revenue")
    chart.click(position={"x": 49, "y": 40})
    expect(page.locator("#financial-quarter")).to_have_value(
        page.locator("#financial-quarter option").first.get_attribute("value"))
    page.get_by_label("Display period").select_option("")
    page.get_by_label("Inspect quarter").select_option("FY2026-Q1")
    expect(page.locator("#metric-revenue")).to_have_text("$44.06B")
    expect(page.locator("#financial-detail")).to_contain_text("0001045810-25-000115")
    expect(page.locator("#financial-table tr[aria-current]")).to_have_count(1)
    page.reload()
    expect(page.locator("#metric-revenue")).to_have_text("$44.06B")
    capture(page, directory, "desktop-financial")

    page.get_by_role("link", name="Chip policy", exact=True).click()
    page.get_by_label("Status", exact=True).select_option("scheduled")
    assert all("Scheduled" in item for item in page.locator("#policy-results .pill").all_text_contents())
    page.goto(home + "#policy?record=POL-011")
    rule = page.locator('[data-record-id="POL-011"]')
    expect(rule).to_have_attribute("open", "")
    expect(rule).to_contain_text("Jan 19, 2027")
    expect(rule.locator(".source-list")).to_contain_text("Bureau of Industry and Security")
    page.goto(home + "#policy?record=POL-016")
    additions = page.locator('[data-record-id="POL-016"]')
    expect(additions).to_have_attribute("open", "")
    expect(additions).to_contain_text("Nov 23, 2026")
    expect(additions).to_contain_text("Nov 25, 2026")

    page.get_by_role("link", name="Technical archive", exact=True).click()
    page.get_by_label("Topic").select_option("cuda")
    expect(page.get_by_role("link", name="Open at 00:06:02")).to_have_attribute(
        "href", "https://www.youtube.com/watch?v=jw_o0xr8MWU&t=362s")
    expect(page.get_by_text("113,101 tokens/s")).to_be_visible()
    expect(page.locator("#benchmark-note")).to_contain_text("8.97%")
    page.get_by_label("Test scenario").select_option("Server")
    expect(page.get_by_text("106,898 tokens/s")).to_be_visible()
    expect(page.get_by_text("103,932 tokens/s")).to_be_visible()
    expect(page.locator("#benchmark-note")).to_contain_text("2.85%")
    page.reload()
    expect(page.get_by_label("Test scenario")).to_have_value("Server")

    page.goto(home)
    with page.expect_download() as item:
        page.get_by_role("button", name="Download the date comparison as PNG").click()
    governance = directory / "governance-figure.png"
    item.value.save_as(governance)
    assert png_size(governance) == (1200, 715)
    assert not errors, errors
    assert not remote, remote


def check_mobile(browser, home, directory):
    for width in (320, 390, 768):
        mobile = browser.new_page(viewport={"width": width, "height": 844},
                                  is_mobile=True, has_touch=True)
        errors = []
        mobile.on("pageerror", lambda error: errors.append(str(error)))
        mobile.goto(home)
        if width == 390:
            capture(mobile, directory, "mobile-home")
        for section in ("timeline", "financials", "policy", "archive"):
            mobile.goto(home + "#" + section)
            expect(mobile.locator("#" + section)).to_be_visible()
            assert mobile.evaluate("document.documentElement.scrollWidth === window.innerWidth"), (section, width)
            if width == 390:
                capture(mobile, directory, "mobile-" + section)
        assert not errors, errors
        mobile.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=ROOT / "observatory/index.html")
    parser.add_argument("--artifacts", type=Path, help="Retain optional screenshots and exported files here")
    args = parser.parse_args()
    with TemporaryDirectory() as scratch, sync_playwright() as playwright:
        destination = args.artifacts or Path(scratch)
        destination.mkdir(parents=True, exist_ok=True)
        browser = playwright.chromium.launch()
        home = args.index.resolve().as_uri()
        check_desktop(browser, home, destination)
        check_mobile(browser, home, destination)
        browser.close()
    print("Offline Chromium checks passed for navigation, filters, permalinks, keyboard, chart selection, exports and mobile widths.")


if __name__ == "__main__":
    main()
