"""Queue NVIDIA filing metadata for editorial review."""
import argparse
import csv
from datetime import date
import io
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from research import ROOT, SOURCE_FIELDS, day, require, rows, unique

CIK = 1045810
FEED_URL = "https://data.sec.gov/submissions/CIK0001045810.json"
FEED_FIELDS = ("accessionNumber", "filingDate", "reportDate", "form", "primaryDocument")
QUEUE_FIELDS = "accession filed_on report_date form primary_document url"
FORMS = {"8-K", "8-K/A", "10-Q", "10-Q/A", "10-K", "10-K/A", "DEF 14A", "DEFA14A", "DEFM14A"}
ACCESSION = r"\d{10}-\d{2}-\d{6}"
CONTACT = r"[^\s@]+@[^\s@]+\.[^\s@]+"
MAX_BYTES = 3_000_000


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(contact):
    require(re.fullmatch(CONTACT, contact), "Set SEC_CONTACT to a project contact email.")
    request = Request(FEED_URL, headers={"User-Agent": f"Jensen Huang Research {contact}",
                                         "Accept": "application/json"})
    with build_opener(NoRedirects()).open(request, timeout=20) as response:
        payload = response.read(MAX_BYTES + 1)
    require(len(payload) <= MAX_BYTES, "EDGAR response exceeds size limit")
    return json.loads(payload)


def filing_record(accession, filed_on, report_date, form, document):
    require(re.fullmatch(ACCESSION, accession), "Invalid EDGAR accession")
    day(filed_on)
    if report_date:
        day(report_date)
    require(form in FORMS and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.htm[l]?", document),
            "Unexpected EDGAR form or primary document")
    url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{accession.replace('-', '')}/{document}"
    return dict(zip(QUEUE_FIELDS.split(), (accession, filed_on, report_date, form, document, url)))


def extract(payload, since, today):
    require(int(payload["cik"]) == CIK, "EDGAR response is for a different issuer")
    recent = payload["filings"]["recent"]
    columns = [recent[key] for key in FEED_FIELDS]
    require(all(isinstance(column, list) for column in columns) and bool(columns[0])
            and len({len(column) for column in columns}) == 1,
            "Empty or malformed EDGAR feed")
    extracted = []
    for accession, filed_on, report_date, form, document in zip(*columns):
        require(day(filed_on) <= today, "EDGAR feed contains a future filing date")
        if form in FORMS and filed_on >= since:
            extracted.append(filing_record(accession, filed_on, report_date, form, document))
    return unique(extracted, lambda row: row["accession"], "EDGAR feed")


def queue(root, payload, today):
    snapshot = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
    require(day(snapshot["as_of"]) <= today, "Snapshot cutoff is after collection date")
    settings = json.loads((root / "watch/settings.json").read_text(encoding="utf-8"))
    since = settings["collect_from"]
    require(day(since) <= day(snapshot["as_of"]), "Collection start is after the snapshot")
    candidates = extract(payload, since, today)
    known = {row["stable_ref"].removeprefix("SEC:") for row in rows(root / "sources/registry.csv", SOURCE_FIELDS)
             if row["stable_ref"].startswith("SEC:")}
    dispositions = unique(rows(root / "watch/dispositions.csv", "accession reviewed_on reason"),
                          lambda row: row["accession"], "review disposition")
    for accession, disposition in dispositions.items():
        require(re.fullmatch(ACCESSION, accession) and disposition["reason"].strip()
                and day(disposition["reviewed_on"]) <= today, "Invalid review disposition")
    queue_path = root / "watch/edgar-candidates.csv"
    existing = unique(rows(queue_path, QUEUE_FIELDS), lambda row: row["accession"], "pending accession")
    for record in existing.values():
        rebuilt = filing_record(*(record[field] for field in QUEUE_FIELDS.split()[:-1]))
        require(record == rebuilt and day(record["filed_on"]) <= today, "Invalid pending filing")
    candidates = existing | candidates
    pending = (row for accession, row in candidates.items()
               if accession not in known and accession not in dispositions)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=QUEUE_FIELDS.split(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(pending, key=lambda row: (row["filed_on"], row["accession"])))
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--date", type=day, help="Fixture collection date")
    parser.add_argument("--output", type=Path, default=ROOT / "watch/edgar-candidates.csv")
    args = parser.parse_args()
    if args.date and not args.fixture:
        parser.error("--date requires --fixture")
    payload = json.loads(args.fixture.read_text(encoding="utf-8")) if args.fixture else fetch(os.getenv("SEC_CONTACT", ""))
    text = queue(ROOT, payload, args.date or date.today())
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(args.output)
    print(f"{len(text.splitlines()) - 1} filing(s) pending editorial review.")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        raise SystemExit(f"EDGAR request failed with HTTP {error.code}; queue retained.") from error
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(f"EDGAR collection stopped; queue retained: {error}") from error
