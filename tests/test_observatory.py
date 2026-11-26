from csv import DictReader
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import re
from shutil import copytree
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import observatory
import research
import verify_upstream


class IndexHTML(HTMLParser):
    """Track stable local entry points and browser assets."""
    def __init__(self):
        super().__init__()
        self.ids = []
        self.local_assets = []
        self.routes = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "script" and "src" in attrs:
            self.local_assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.local_assets.append(attrs["href"])
        if tag == "a" and "data-view" in attrs:
            self.routes.append((attrs["data-view"], attrs["href"]))


class ObservatoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = observatory.load_site()

    def snapshot_copy(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / "repository"
        return copytree(research.ROOT, root, ignore=lambda _dir, names: {".git", "__pycache__"} & set(names))

    def test_generated_snapshot_and_download_match_repo(self):
        expected = observatory.snapshot_script()
        self.assertEqual((research.ROOT / "observatory/data.js").read_text(), expected)
        for name, content in self.payload["downloads"].items():
            self.assertEqual(content, (research.ROOT / "data" / name).read_text())
            self.assertTrue(list(DictReader(content.splitlines())))

    def test_public_timeline_selects_the_filing_as_primary(self):
        row = next(row for row in self.payload["timeline"] if row["id"] == "EV-014")
        source = self.payload["sources"][row["primary_source_id"]]
        self.assertEqual(row["event_date"], "2026-11-22")
        self.assertEqual(row["disclosed_on"], "2026-11-23")
        self.assertEqual(source["stable_ref"], "SEC:0001045810-26-000090")

    def test_quarterly_series_reconciles_and_keeps_exact_recent_numbers(self):
        fin = self.payload["financials"]
        self.assertLessEqual(fin[0]["period_end"], "2020-04-26")
        self.assertGreaterEqual(fin[-1]["period_end"], "2026-10-25")
        self.assertGreaterEqual(len(fin), 27)
        q3 = next(row for row in fin if row["period_end"] == "2026-10-25")
        self.assertEqual(q3["data_center_usd_m"], "107610")
        self.assertEqual(q3["market_source_id"], "SRC-043")
        self.assertEqual(q3["gaap_rd_usd_m"], "7454")

    def test_false_quarterly_amount_fails_reconciliation(self):
        path = self.snapshot_copy()
        report = path / "data/quarterly_financials.csv"
        report.write_text(report.read_text().replace("3080,1141,735", "3080,1111,735"))
        with self.assertRaisesRegex(ValueError, "does not reconcile"):
            research.validate(path)

    def test_market_source_must_have_a_reviewed_locator(self):
        path = self.snapshot_copy()
        report = path / "data/quarterly_financials.csv"
        report.write_text(report.read_text().replace("SRC-100,SRC-040", "SRC-100,SRC-005"))
        with self.assertRaisesRegex(ValueError, "market source"):
            research.validate(path)

    def test_policy_schedule_must_match_the_timeline(self):
        path = self.snapshot_copy()
        policy = path / "data/policy_tracker.csv"
        policy.write_text(policy.read_text().replace(",,,2026-12-03,Senate Banking", ",,,2026-12-04,Senate Banking"))
        lookup = {row["id"]: row for row in self.payload["timeline"]}
        with self.assertRaisesRegex(ValueError, "schedule date disagrees"):
            observatory.policy_data(path, self.payload["claims"], lookup, date(2026, 11, 26))

    def test_policy_records_cannot_be_published_after_cutoff(self):
        path = self.snapshot_copy()
        policy = path / "data/policy_tracker.csv"
        policy.write_text(policy.read_text().replace("2026-11-25,,,,Senator", "2026-11-27,,,,Senator"))
        with self.assertRaisesRegex(ValueError, "beyond cutoff"):
            observatory.load_site(path)

    def test_archive_timestamp_must_have_a_video_source(self):
        path = self.snapshot_copy()
        archive = path / "data/archive_index.csv"
        archive.write_text(archive.read_text().replace("SRC-050,,5:38", "SRC-050,1,5:38"))
        with self.assertRaisesRegex(ValueError, "unsupported timestamp"):
            observatory.load_site(path)

    def test_benchmark_uses_matched_scenarios(self):
        path = self.snapshot_copy()
        case = path / "data/benchmark_comparison.csv"
        case.write_text(case.read_text().replace(",Offline,", ",Interactive,", 1))
        with self.assertRaisesRegex(ValueError, "incompatible workloads"):
            observatory.load_site(path)

    def test_benchmark_audit_requires_the_pinned_source(self):
        path = self.snapshot_copy() / "incorrect.csv"
        path.write_text("Location,Result\n")
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_upstream.audit_benchmark(path, self.payload["benchmarks"])

    def test_reader_handles_both_issuer_market_table_layouts(self):
        classic = "($ in millions)   Q2 FY22   Q1 FY22\nData Center 2,366 2,048\nTOTAL 6,507 5,661"
        grouped = "Fiscal 2026  Fiscal 2027\n($ in millions) Q1 Q2 Q1\nData Center 10 20 30\nTOTAL 50 60 70"
        self.assertEqual(verify_upstream.market_trend_rows(classic), {
            ("2022", "2"): (6507, 2366), ("2022", "1"): (5661, 2048),
        })
        self.assertEqual(verify_upstream.market_trend_rows(grouped)[("2027", "1")], (70, 30))
        with self.assertRaisesRegex(ValueError, "amount count"):
            verify_upstream.market_trend_rows(grouped.replace("50 60 70", "50 60"))

    def test_page_has_unique_ids_and_local_assets(self):
        assets = research.ROOT / "observatory"
        page = IndexHTML()
        page.feed((assets / "index.html").read_text())
        self.assertEqual(len(page.ids), len(set(page.ids)))
        self.assertEqual({route for route, _ in page.routes}, {"timeline", "financials", "policy", "archive"})
        for route, anchor in page.routes:
            self.assertIn(route, page.ids)
            self.assertEqual(anchor, "#" + route)
        for name in page.local_assets:
            self.assertFalse(re.match(r"\w+://", name))
            self.assertTrue((assets / name).is_file())


if __name__ == "__main__":
    unittest.main()
