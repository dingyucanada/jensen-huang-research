"""Validate the observatory datasets and build the offline-friendly browser snapshot."""
import argparse
import json
from decimal import Decimal
from pathlib import Path
import re
from urllib.parse import urlsplit

from research import ROOT, day, dated, require, rows, unique, validate
from verify_upstream import BENCHMARK_FIELDS

POLICY_FIELDS = (
    "id kind status jurisdiction published_on effective_on next_on reference title summary event_id claim_id"
)
ARCHIVE_FIELDS = "id topic event_date title presenter source_id timestamp_seconds locator summary claim_id"
MILESTONE_FIELDS = "id event_date title summary event_id claim_id"
POLICY_KINDS = {"rule", "disclosure", "agency_action", "oversight", "enforcement"}
SCHEDULED_STATES = {"scheduled", "rescheduled"}
TERMINAL_STATES = {"held", "canceled"}
POLICY_STATES = {"historical", "superseded", "reported", "issued", "open", "effective", "requested"} | \
    SCHEDULED_STATES | TERMINAL_STATES
ARCHIVE_TOPICS = {"oral_history", "founding", "cuda", "engineering", "leadership"}
MODEL_MATCH = ("round", "division", "availability", "system_type", "model", "accelerators")
BENCHMARK_SCENARIOS = {"Offline", "Server"}


def validate_evidence(row, claims, statuses):
    claim = claims.get(row["claim_id"])
    require(claim is not None and claim["status"] in statuses, f"{row['id']}: invalid claim")
    if "source_id" in row:
        require(row["source_id"] in {item["source_id"] for item in claim["evidence"]},
                f"{row['id']}: source is absent from the claim")


def validate_dataset(path, fields, prefix, required):
    records = rows(path, fields)
    unique(records, lambda row: row["id"], path.name)
    for row in records:
        require(re.fullmatch(rf"{prefix}-\d{{3,}}", row["id"])
                and all(row[key].strip() for key in required),
                f"{row['id']}: missing or invalid fields in {path.name}")
    return records


def policy_data(root, claims, event_lookup, cutoff):
    entries = validate_dataset(root / "data/policy_tracker.csv", POLICY_FIELDS, "POL",
                               ("title", "summary", "jurisdiction"))
    for row in entries:
        is_scheduled = row["status"] in SCHEDULED_STATES
        validate_evidence(row, claims, {"scheduled"} if is_scheduled else {"documented", "attributed"})
        eid = row["event_id"]
        require(eid in event_lookup and event_lookup[eid]["category"] == "policy",
                f"{row['id']}: unlinked policy event")
        require(row["kind"] in POLICY_KINDS and row["status"] in POLICY_STATES,
                f"{row['id']}: invalid policy kind or status")
        dates = {key: day(row[key]) for key in ("published_on", "effective_on", "next_on") if row[key]}
        if is_scheduled:
            event = event_lookup[eid]
            require(row["kind"] == "oversight" and row["next_on"] == event["event_date"]
                    and event["status"] == "scheduled",
                    f"{row['id']}: schedule date disagrees with timeline")
        if row["status"] in TERMINAL_STATES:
            event = event_lookup[eid]
            require(row["kind"] == "oversight" and row["next_on"] == event["event_date"]
                    and event["status"] == "documented" and dates["next_on"] <= cutoff,
                    f"{row['id']}: completed or canceled event needs a dated record")
        require(dates.get("published_on", cutoff) <= cutoff, f"{row['id']}: publication is beyond cutoff")
        if row["status"] == "effective":
            require("effective_on" in dates and dates["effective_on"] <= cutoff,
                    f"{row['id']}: effective date after cutoff or missing")
        if "effective_on" in dates and "next_on" in dates:
            require(dates["effective_on"] <= dates["next_on"], f"{row['id']}: invalid follow-up date")
    return entries


def archive_data(root, sources, claims, event_lookup, cutoff):
    entries = validate_dataset(root / "data/archive_index.csv", ARCHIVE_FIELDS, "ARC",
                               ("title", "presenter", "locator", "summary"))
    for row in entries:
        validate_evidence(row, claims, {"attributed", "documented"})
        dated(row["event_date"])
        require(row["topic"] in ARCHIVE_TOPICS and row["event_date"] <= cutoff[:len(row["event_date"])],
                f"{row['id']}: invalid archive topic or date")
        if row["timestamp_seconds"]:
            seconds = row["timestamp_seconds"]
            url = urlsplit(sources[row["source_id"]]["url"])
            require(seconds.isdecimal() and 0 <= int(seconds) <= 86400
                    and url.hostname in {"www.youtube.com", "youtube.com"} and url.path == "/watch",
                    f"{row['id']}: unsupported timestamp")
    milestones = validate_dataset(root / "data/technology_milestones.csv", MILESTONE_FIELDS, "TEC",
                                  ("title", "summary", "event_date"))
    for row in milestones:
        validate_evidence(row, claims, {"attributed", "documented"})
        event = event_lookup.get(row["event_id"])
        require(event is not None and event["category"] == "technology"
                and event["event_date"] == row["event_date"] and event["claim_id"] == row["claim_id"],
                f"{row['id']}: technology milestone disagrees with timeline")
    return entries, milestones


def benchmark_data(root, claims):
    records = validate_dataset(root / "data/benchmark_comparison.csv", BENCHMARK_FIELDS, "BMARK",
                               ("submitter", "platform", "model", "upstream_locator", "accelerator"))
    require(len(records) == 4 and {row["scenario"] for row in records} == BENCHMARK_SCENARIOS,
            "Benchmark comparison mixes incompatible workloads or scenarios")
    for row in records:
        validate_evidence(row, claims, {"derived"})
        rate = Decimal(row["throughput_tokens_s"])
        require(rate.is_finite() and rate > 0 and int(row["accelerators"]) > 0,
                f"{row['id']}: invalid throughput or accelerator count")
    unique(records, lambda row: (row["platform"], row["scenario"]), "benchmark scenario per platform")
    require(len({tuple(row[field] for field in MODEL_MATCH) for row in records}) == 1
            and len({row["platform"] for row in records}) == 2,
            "Benchmark comparison mixes incompatible workloads or systems")
    return records


def load_site(root=ROOT):
    snapshot, sources, claims, annual, quarterly, timeline, _ = validate(root)
    cutoff = snapshot["as_of"]
    lookup = {row["id"]: row for row in timeline}
    policies = policy_data(root, claims, lookup, day(cutoff))
    archive, milestones = archive_data(root, sources, claims, lookup, cutoff)
    benchmarks = benchmark_data(root, claims)
    return {
        "snapshot": snapshot,
        "sources": sources,
        "claims": claims,
        "timeline": sorted(timeline, key=lambda row: (row["event_date"], row["id"]), reverse=True),
        "financials": sorted(quarterly, key=lambda row: row["period_end"]),
        "policies": sorted(policies, key=lambda row: row["published_on"] or row["next_on"], reverse=True),
        "archive": archive,
        "milestones": sorted(milestones, key=lambda row: row["event_date"]),
        "benchmarks": benchmarks,
        "downloads": {
            name: (root / "data" / name).read_text(encoding="utf-8")
            for name in ("timeline.csv", "quarterly_financials.csv", "annual_financials.csv",
                         "policy_tracker.csv", "archive_index.csv", "technology_milestones.csv",
                         "benchmark_comparison.csv")
        },
    }


def snapshot_script(root=ROOT):
    payload = json.dumps(load_site(root), ensure_ascii=False, separators=(",", ":"))
    # External script, no execution of embedded source text.
    return "// Generated from the repository. Edit the CSV or JSON records, then run scripts/observatory.py build.\n" \
           f"window.observatoryData = {payload};\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "check"))
    args = parser.parse_args()
    file = ROOT / "observatory/data.js"
    rendered = snapshot_script()
    if args.action == "build":
        file.write_text(rendered, encoding="utf-8")
    else:
        require(file.read_text(encoding="utf-8") == rendered,
                "Browser snapshot is stale. Run python3 scripts/observatory.py build.")
    print("Observatory data, ledgers and browser snapshot verified.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, ArithmeticError, OSError) as error:
        raise SystemExit(str(error)) from error
