import csv
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
from shutil import copytree
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_source_urls
import edgar_watch
import research


class ResearchTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        copytree(research.ROOT, self.root, ignore=lambda _dir, names: {".git", "__pycache__"} & set(names))

    def test_index_is_reproducible(self):
        for name, lines in research.render(self.root).items():
            self.assertEqual((self.root / name).read_text(), "\n".join(lines).rstrip() + "\n")
        self.assertGreater(research.check_links(self.root), 0)

    def test_market_correction_matches_price_data(self):
        *_, market = research.validate(self.root)
        calculated = research.market_returns(market)
        self.assertEqual(calculated["SOXX"][1].quantize(Decimal(".01")), Decimal("13.63"))
        self.assertEqual((calculated["NVDA"][1] - calculated["SOXX"][1]).quantize(Decimal(".01")),
                         Decimal("17.85"))

    def test_bad_data_source_is_rejected(self):
        path = self.root / "data/annual_financials.csv"
        path.write_text(path.read_text().replace("CLM-009,SRC-011", "CLM-009,SRC-001", 1))
        with self.assertRaisesRegex(ValueError, "row source missing"):
            research.validate(self.root)

    def test_future_event_requires_scheduled_status(self):
        path = self.root / "data/timeline.csv"
        path.write_text(path.read_text().replace("2026-11-25,2026-11-25,day", "2026-11-27,2026-11-25,day"))
        with self.assertRaisesRegex(ValueError, "future event treated as fact"):
            research.validate(self.root)

    def test_unknown_source_in_claim_is_rejected(self):
        path = self.root / "sources/claims.json"
        path.write_text(path.read_text().replace('"SRC-001"', '"SRC-999"', 1))
        with self.assertRaisesRegex(ValueError, "unknown source"):
            research.validate(self.root)

    def test_broken_heading_is_rejected(self):
        path = self.root / "test-link.md"
        path.write_text("[claim](sources/evidence.md#missing)\n")
        with self.assertRaisesRegex(ValueError, "missing heading"):
            research.check_links(self.root)

    def test_queue_filters_and_keeps_unresolved_rows(self):
        feed = json.loads((self.root / "tests/fixtures/edgar.json").read_text())
        today = date(2026, 11, 30)
        (self.root / "watch/settings.json").write_text('{"collect_from": "2026-11-23"}\n')
        proposed = edgar_watch.queue(self.root, feed, today)
        entries = list(csv.DictReader(proposed.splitlines()))
        self.assertEqual([entry["accession"] for entry in entries], ["0001045810-26-000999"])
        queue = self.root / "watch/edgar-candidates.csv"
        queue.write_text(proposed)
        recent = feed["filings"]["recent"]
        feed["filings"]["recent"] = {key: values[1:] for key, values in recent.items()}
        self.assertEqual(edgar_watch.queue(self.root, feed, today), proposed)
        (self.root / "watch/dispositions.csv").write_text(
            "accession,reviewed_on,reason\n0001045810-26-000999,2026-11-30,Test disposition\n"
        )
        self.assertEqual(len(edgar_watch.queue(self.root, feed, today).splitlines()), 1)

    def test_invalid_filing_filename_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "primary document"):
            edgar_watch.filing_record("0001045810-26-000999", "2026-11-30", "", "8-K", "../../file.htm")

    def test_unknown_filer_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "different issuer"):
            edgar_watch.extract({"cik": 1}, "2026-11-26", date(2026, 11, 30))

    def test_link_probe_retries_with_get_on_head_404(self):
        source = {"id": "SRC-001", "url": "https://example.com/document"}
        with patch.object(check_source_urls, "public_https"), \
                patch.object(check_source_urls, "check_url", side_effect=[404, 200]) as probe:
            self.assertEqual(check_source_urls.check(source), ("SRC-001", "OK", 200))
            self.assertEqual([call.args[1].get_method() for call in probe.call_args_list], ["HEAD", "GET"])


if __name__ == "__main__":
    unittest.main()
