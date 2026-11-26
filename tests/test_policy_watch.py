import csv
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from shutil import copytree
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import policy_watch

TODAY = date(2026, 11, 26)
SINCE = "2026-11-19"


class PolicyWatchTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "sample"
        for folder in ("sources", "watch"):
            copytree(policy_watch.ROOT / folder, self.root / folder)
        self.feed = json.loads((policy_watch.ROOT / "tests/fixtures/federal-register.json").read_text())

    def test_queues_unreviewed_documents_once(self):
        output = policy_watch.queue(self.root, [self.feed, self.feed], TODAY, SINCE)
        entries = list(csv.DictReader(output.splitlines()))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["document_number"], "2026-55555")
        self.assertEqual(entries[0]["source_url"], "https://www.federalregister.gov/d/2026-55555")

    def test_persists_candidate_after_feed_window_and_retires_disposition(self):
        dest = self.root / "watch/federal-register-candidates.csv"
        dest.write_text(policy_watch.queue(self.root, [self.feed], TODAY, SINCE))
        later = date(2027, 2, 1)
        empty = {"count": 0, "results": []}
        self.assertIn("2026-55555", policy_watch.queue(self.root, [empty], later, "2027-01-01"))
        dispositions = self.root / "watch/federal-register-dispositions.csv"
        dispositions.write_text("document_number,reviewed_on,reason\n2026-55555,2026-11-26,Outside scope\n")
        self.assertEqual(len(policy_watch.queue(self.root, [empty], later, "2027-01-01").splitlines()), 1)

    def test_rejects_partial_result_instead_of_silently_dropping_records(self):
        self.feed["count"] += 1
        with self.assertRaisesRegex(ValueError, "partial or malformed"):
            policy_watch.queue(self.root, [self.feed], TODAY, SINCE)

    def test_rejects_inconsistent_metadata_for_same_document(self):
        conflict = deepcopy(self.feed)
        conflict["results"][-1]["title"] = "Conflicting date or identity"
        with self.assertRaisesRegex(ValueError, "Conflicting results"):
            policy_watch.queue(self.root, [self.feed, conflict], TODAY, SINCE)

    def test_rejects_csv_formula_and_future_record(self):
        with self.assertRaisesRegex(ValueError, "candidate title"):
            policy_watch.candidate("2026-99999", "2026-11-25", "Rule", '=HYPERLINK("example")', TODAY)
        with self.assertRaisesRegex(ValueError, "candidate metadata"):
            policy_watch.candidate("2026-99999", "2026-11-27", "Rule", "Future rule", TODAY)


if __name__ == "__main__":
    unittest.main()
