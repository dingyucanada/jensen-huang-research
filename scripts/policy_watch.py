"""Queue candidate BIS publications for review using Federal Register metadata."""
import argparse
import csv
from datetime import date, timedelta
import io
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from edgar_watch import NoRedirects
from research import ROOT, SOURCE_FIELDS, day, require, rows, unique

API = "https://www.federalregister.gov/api/v1/documents.json"
DISCOVERY_TERMS = ("advanced computing", "semiconductor")
CANDIDATE_FIELDS = "document_number published_on document_type title source_url"
DOCUMENT = r"\d{4}-\d{4,6}"
TYPES = {"Rule", "Proposed Rule", "Notice", "Presidential Document"}
RESULT_LIMIT = 100


def fetch(term, since, today):
    params = [
        ("conditions[agencies][]", "industry-and-security-bureau"),
        ("conditions[publication_date][gte]", since),
        ("conditions[publication_date][lte]", today.isoformat()),
        ("conditions[term]", term),
        ("per_page", RESULT_LIMIT),
        *[("fields[]", field) for field in ("document_number", "publication_date", "type", "title")],
    ]
    headers = {"User-Agent": "NVIDIA Evidence Observatory (public research)", "Accept": "application/json"}
    request = Request(API + "?" + urlencode(params), headers=headers)
    with build_opener(NoRedirects()).open(request, timeout=20) as reply:
        content = reply.read(500_001)
    require(len(content) <= 500_000, "Federal Register response exceeds size limit")
    return json.loads(content)


def candidate(number, published, document_type, title, cutoff):
    require(re.fullmatch(DOCUMENT, number) and day(published) <= cutoff and document_type in TYPES,
            "Invalid Federal Register candidate metadata")
    require(isinstance(title, str) and 1 <= len(title) <= 500
            and title == title.strip() and not re.search(r"[\x00-\x1f\x7f]", title)
            and title[0] not in "=+@-", "Invalid Federal Register candidate title")
    return dict(zip(CANDIDATE_FIELDS.split(),
                    (number, published, document_type, title, f"https://www.federalregister.gov/d/{number}")))


def collect(payloads, since, today):
    records = {}
    for payload in payloads:
        results = payload["results"]
        require(isinstance(results, list) and payload["count"] == len(results) <= RESULT_LIMIT,
                "Federal Register returned a partial or malformed result set")
        for row in results:
            number = row["document_number"]
            result = candidate(number, row["publication_date"], row["type"], row["title"], today)
            require(result["published_on"] >= since, "Result predates requested discovery window")
            require(number not in records or records[number] == result, "Conflicting results for the same document")
            records[number] = result
    return records


def queue(root, payloads, today, since):
    require(day(since) <= today, "Policy discovery window starts after collection date")
    known = {row["stable_ref"].removeprefix("FR:") for row in rows(root / "sources/registry.csv", SOURCE_FIELDS)
             if row["stable_ref"].startswith("FR:")}
    resolved = unique(rows(root / "watch/federal-register-dispositions.csv", "document_number reviewed_on reason"),
                      lambda row: row["document_number"], "policy disposition")
    for identifier, row in resolved.items():
        require(re.fullmatch(DOCUMENT, identifier) and day(row["reviewed_on"]) <= today and row["reason"].strip(),
                "Invalid Federal Register disposition")
    existing = unique(rows(root / "watch/federal-register-candidates.csv", CANDIDATE_FIELDS),
                      lambda row: row["document_number"], "pending policy candidate")
    for identifier, row in existing.items():
        require(row == candidate(identifier, row["published_on"], row["document_type"], row["title"], today),
                "Invalid Federal Register metadata in queue")
    current = existing | collect(payloads, since, today)
    pending = (item for number, item in current.items() if number not in known and number not in resolved)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CANDIDATE_FIELDS.split(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(pending, key=lambda record: (record["published_on"], record["document_number"])))
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, action="append", help="Use saved results for a test run")
    parser.add_argument("--date", type=day, help="Collection date for fixtures")
    parser.add_argument("--output", type=Path, default=ROOT / "watch/federal-register-candidates.csv")
    args = parser.parse_args()
    if args.date and not args.fixture:
        parser.error("--date requires --fixture")
    settings = json.loads((ROOT / "watch/policy-settings.json").read_text(encoding="utf-8"))
    today = args.date or date.today()
    since = max(day(settings["collect_from"]), today - timedelta(days=60)).isoformat()
    require(day(since) <= today, "Discovery window starts after today")
    payloads = ([json.loads(path.read_text(encoding="utf-8")) for path in args.fixture]
                if args.fixture else [fetch(term, since, today) for term in DISCOVERY_TERMS])
    result = queue(ROOT, payloads, today, since)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(result, encoding="utf-8")
    temp.replace(args.output)
    print(f"{len(result.splitlines()) - 1} Federal Register record(s) pending review.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Policy discovery stopped; prior queue retained: {error}") from error
