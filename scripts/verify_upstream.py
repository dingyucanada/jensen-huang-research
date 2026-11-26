"""Compare the published snapshot with user-supplied SEC and MLCommons source files."""
import argparse
from decimal import Decimal
from hashlib import sha256
import csv
import json
from pathlib import Path
import re
import subprocess

from research import ROOT, day, require, rows, validate

BENCHMARK_FIELDS = (
    "id round division availability system_type model scenario accelerators submitter platform "
    "accelerator throughput_tokens_s upstream_locator source_id claim_id"
)
BENCHMARK_SHA256 = "87980a2dfba85139ca806b63634305bcbc4ad6803bf2d520351e022ba905065a"


def audit_benchmark(path, benchmarks):
    require(sha256(path.read_bytes()).hexdigest() == BENCHMARK_SHA256,
            "MLCommons CSV does not match the pinned snapshot")
    with path.open(encoding="utf-8", newline="") as content:
        upstream = list(csv.DictReader(content))
    for record in benchmarks:
        found = [row for row in upstream if row["Location"] == record["upstream_locator"]]
        require(len(found) == 1, f"{record['id']}: expected one upstream result")
        result = found[0]
        pairs = {
            "round": "version", "division": "Division", "availability": "Availability",
            "system_type": "SystemType", "model": "Model", "scenario": "Scenario",
            "accelerators": "total_accelerators", "submitter": "Organization", "platform": "Platform",
            "accelerator": "accelerator_model_name",
        }
        require(all(record[key] == result[field] for key, field in pairs.items())
                and Decimal(record["throughput_tokens_s"]) == Decimal(result["Result"])
                and result["Units"] == "Tokens/s" and result["inferred"] == "0" and result["errors"] == "0",
                f"{record['id']}: published values no longer match the upstream snapshot")
    return len(benchmarks)


def gaap_amounts(facts, tags, end, min_days, max_days, cutoff):
    values = set()
    for tag in tags:
        for fact in facts.get(tag, {}).get("units", {}).get("USD", []):
            if (fact.get("end") == end and fact.get("start") and fact.get("filed", "9999-12-31") <= cutoff
                    and min_days <= (day(end) - day(fact["start"])).days + 1 <= max_days):
                values.add(Decimal(fact["val"]) / 1_000_000)
    return values


def audit_companyfacts(path, quarterly, cutoff):
    """Use three-month facts, or annual less nine-month facts for Q4."""
    contents = json.loads(path.read_text(encoding="utf-8"))
    require(int(contents["cik"]) == 1045810, "Company Facts file is for a different issuer")
    facts = contents["facts"]["us-gaap"]
    fields = {
        "revenue_usd_m": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        "gaap_rd_usd_m": ("ResearchAndDevelopmentExpense",),
    }
    checked, missing = [], []
    by_period = {(row["fiscal_year"], row["quarter"]): row["period_end"] for row in quarterly}
    for row in quarterly:
        year, quarter, end = (row[key] for key in ("fiscal_year", "quarter", "period_end"))
        label = f"FY{year} Q{quarter}"
        verified = 0
        for field, tags in fields.items():
            if quarter == "4":
                q3_end = by_period.get((year, "3"))
                if not q3_end:
                    continue
                full_year = gaap_amounts(facts, tags, end, 360, 375, cutoff)
                nine_months = gaap_amounts(facts, tags, q3_end, 265, 280, cutoff)
                amounts = {annual - ytd for annual in full_year for ytd in nine_months}
            else:
                amounts = gaap_amounts(facts, tags, end, 85, 98, cutoff)
            if not amounts:
                continue
            require(any(abs(value - Decimal(row[field])) <= 1 for value in amounts),
                    f"{label}: {field} differs from Company Facts by more than USD 1M")
            verified += 1
        (checked if verified == len(fields) else missing).append(label)
    return checked, missing


def market_trend_rows(text):
    """Read the labeled Data Center and TOTAL rows from a layout-preserved issuer PDF."""
    heading = re.search(r"^\s*\(\$ in millions\)(.*)$", text, re.MULTILINE)
    dc = re.search(r"^\s*Data Center\s+([^\n]+)$", text, re.MULTILINE)
    total = re.search(r"^\s*TOTAL\s+([^\n]+)$", text, re.MULTILINE)
    require(heading and dc and total, "Missing labeled market-table rows")

    columns = re.findall(r"Q([1-4])\s+FY(\d{2,4})", heading.group(1))
    if columns:
        periods = [(str(2000 + int(year)) if len(year) == 2 else year, quarter)
                   for quarter, year in columns]
    else:
        years = re.findall(r"Fiscal (20\d{2})", text[:heading.start()])
        quarters = re.findall(r"Q([1-4])", heading.group(1))
        first_quarters = [position for position, quarter in enumerate(quarters) if quarter == "1"]
        require(len(years) == len(first_quarters) and first_quarters[:1] == [0],
                "Market-table fiscal headings are ambiguous")
        periods = []
        year_index = -1
        for quarter in quarters:
            if quarter == "1":
                year_index += 1
            periods.append((years[year_index], quarter))
    totals, data_center = (
        [int(value.replace(",", "")) for value in re.findall(r"[0-9][0-9,]*", row.group(1))]
        for row in (total, dc)
    )
    require(len(periods) == len(set(periods)) == len(totals) == len(data_center) > 0,
            "Market-table amount count does not match the quarterly labels")
    return dict(zip(periods, zip(totals, data_center)))


def audit_market_table(path, quarterly, sid):
    matching = [row for row in quarterly if row["market_source_id"] == sid]
    require(bool(matching), f"{sid}: no quarterly rows cite this market table")
    text = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)
    raw = market_trend_rows(text)
    for row in matching:
        key = row["fiscal_year"], row["quarter"]
        expected = int(row["revenue_usd_m"]), int(row["data_center_usd_m"])
        require(raw.get(key) == expected, f"FY{key[0]} Q{key[1]}: market table amounts differ")
    return len(matching)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mlperf", type=Path, help="Pinned MLCommons summary.csv downloaded separately")
    parser.add_argument("--companyfacts", type=Path, help="NVIDIA SEC Company Facts JSON")
    parser.add_argument("--market-table", action="append", default=[], metavar="SRC-ID=PATH",
                        help="Check an NVIDIA market table PDF using pdftotext, repeatable")
    args = parser.parse_args()
    if not (args.mlperf or args.companyfacts or args.market_table):
        parser.error("provide --mlperf, --companyfacts or --market-table")
    snapshot, _, _, _, quarterly, _, _ = validate()
    if args.mlperf:
        benchmarks = rows(ROOT / "data/benchmark_comparison.csv", BENCHMARK_FIELDS)
        print(f"{audit_benchmark(args.mlperf, benchmarks)} MLCommons rows verified against the pinned CSV.")
    if args.companyfacts:
        checked, missing = audit_companyfacts(args.companyfacts, quarterly, snapshot["as_of"])
        require(bool(checked), "No quarterly facts could be matched")
        print(f"Two GAAP amounts cross-checked for {len(checked)} quarters.")
        if missing:
            print("Remaining earnings-release observations: " + ", ".join(missing))
    audited_tables = set()
    for table in args.market_table:
        sid, sep, path = table.partition("=")
        require(sep and sid not in audited_tables, "Expected each market table as a distinct SRC-ID=PATH")
        audited_tables.add(sid)
        print(f"{sid}: {audit_market_table(Path(path), quarterly, sid)} quarterly market observations verified.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, ArithmeticError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
