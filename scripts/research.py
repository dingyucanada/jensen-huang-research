"""Validate the evidence repository and regenerate its public indexes."""
import argparse
import csv
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
POLICIES = {
    "documented": {"filing", "issuer", "government", "institutional", "research"},
    "attributed": {"filing", "issuer", "government", "institutional", "interview", "journalism"},
    "scheduled": {"filing", "issuer", "government", "institutional"},
    "derived": {"filing", "market_data", "research"},
    "interpretation": {"filing", "issuer", "government", "institutional", "research", "interview"},
    "unverified": set(),
}
SOURCE_FIELDS = "id published_on kind publisher title stable_ref url accessed_on"
CLAIM_FIELDS = {"id", "status", "statement", "evidence", "boundary", "reviewed_on"}
DATE_PATTERNS = {"year": r"\d{4}", "month": r"\d{4}-\d{2}", "day": r"\d{4}-\d{2}-\d{2}"}
LINK = re.compile(r"!?\[[^\]\n]+\]\((<[^<>\s]+>|[^()<>\s]+)\)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rows(path, fields):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == fields.split(), f"{path.name}: unexpected header")
        entries = list(reader)
    require(all(None not in row and None not in row.values() for row in entries),
            f"{path.name}: malformed row")
    return entries


def day(value):
    require(re.fullmatch(DATE_PATTERNS["day"], value), f"Invalid date: {value}")
    return date.fromisoformat(value)


def dated(value):
    day(value + {4: "-01-01", 7: "-01", 10: ""}.get(len(value), ""))


def unique(entries, key, label):
    indexed = {key(row): row for row in entries}
    require(len(entries) == len(indexed), f"{label}: duplicate key")
    return indexed


def valid_https(url):
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and bool(parsed.hostname)
            and parsed.username is None and parsed.port in (None, 443)
            and not re.search(r"\s", url))


def validate(root=ROOT):
    snapshot = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
    cutoff = day(snapshot["as_of"])
    require(re.fullmatch(r"\d+\.\d+\.\d+", snapshot["version"]), "Invalid version")
    sources = unique(rows(root / "sources/registry.csv", SOURCE_FIELDS),
                     lambda row: row["id"], "source")
    unique(list(sources.values()), lambda row: row["url"], "source URL")
    for sid, source in sources.items():
        require(re.fullmatch(r"SRC-\d{3,}", sid), f"Invalid source ID: {sid}")
        require(source["kind"] in set.union(*POLICIES.values()), f"{sid}: unknown source kind")
        require(source["publisher"].strip() and source["title"].strip()
                and valid_https(source["url"]), f"{sid}: incomplete source")
        accessed = day(source["accessed_on"])
        require(accessed <= cutoff, f"{sid}: accessed after cutoff")
        if published := source["published_on"]:
            dated(published)
            require(published <= accessed.isoformat()[:len(published)], f"{sid}: future publication")
        if source["stable_ref"].startswith("SEC:"):
            accession = source["stable_ref"].removeprefix("SEC:")
            require(re.fullmatch(r"0001045810-\d{2}-\d{6}", accession)
                    and f"/{accession.replace('-', '')}/" in source["url"],
                    f"{sid}: SEC accession disagrees with URL")
    claims = unique(json.loads((root / "sources/claims.json").read_text(encoding="utf-8")),
                    lambda row: row["id"], "claim")
    for cid, claim in claims.items():
        require(re.fullmatch(r"CLM-\d{3,}", cid) and set(claim) == CLAIM_FIELDS,
                f"{cid}: invalid claim fields")
        reviewed = day(claim["reviewed_on"])
        status = claim["status"]
        require(status in POLICIES and reviewed <= cutoff and claim["statement"].strip()
                and claim["boundary"].strip(), f"{cid}: incomplete claim")
        evidence = claim["evidence"]
        referenced = unique(evidence, lambda item: item["source_id"], cid)
        for sid, item in referenced.items():
            require(set(item) == {"source_id", "locator"} and sid in sources and item["locator"].strip(),
                    f"{cid}: unknown source or missing locator ({sid})")
            require(day(sources[sid]["accessed_on"]) <= reviewed, f"{cid}: source accessed after review")
        if status != "unverified":
            require(any(sources[sid]["kind"] in POLICIES[status] for sid in referenced),
                    f"{cid}: no qualifying evidence for {status}")

    def verify_provenance(row, statuses):
        cid = row["claim_id"]
        require(cid in claims and claims[cid]["status"] in statuses, f"{cid}: invalid dataset claim")
        if "source_id" in row:
            require(row["source_id"] in {e["source_id"] for e in claims[cid]["evidence"]},
                    f"{cid}: row source missing from evidence")

    data = root / "data"
    annual = rows(data / "annual_financials.csv",
                  "fiscal_year period_end revenue_usd_m data_center_usd_m gaap_rd_usd_m claim_id source_id")
    quarterly = rows(data / "quarterly_financials.csv",
                     "fiscal_year quarter period_end revenue_usd_m data_center_usd_m_rounded gaap_rd_usd_m claim_id source_id")
    unique(annual, lambda row: int(row["fiscal_year"]), "annual fiscal year")
    unique(quarterly, lambda row: (int(row["fiscal_year"]), int(row["quarter"])), "fiscal quarter")
    for row in annual + quarterly:
        verify_provenance(row, {"documented"})
        period = day(row["period_end"])
        fiscal_year = int(row["fiscal_year"])
        source = sources[row["source_id"]]
        require(source["kind"] == "filing" and period <= day(source["published_on"]),
                f"{row['period_end']}: invalid financial provenance")
        if "quarter" in row:
            quarter = int(row["quarter"])
            require(1 <= quarter <= 4 and period.year in (fiscal_year - 1, fiscal_year),
                    f"{row['period_end']}: invalid fiscal quarter")
        else:
            require(period.year == fiscal_year and period.month == 1, "Invalid annual fiscal year end")
        revenue = int(row["revenue_usd_m"])
        data_center = int(row.get("data_center_usd_m", row.get("data_center_usd_m_rounded")))
        require(revenue > 0 and 0 <= data_center <= revenue and int(row["gaap_rd_usd_m"]) >= 0,
                f"{row['period_end']}: invalid financial amounts")
    require(len(annual) >= 2, "Annual series requires at least two rows")
    ownership = rows(data / "ownership.csv", "as_of person beneficial_shares percent_reported claim_id source_id")
    unique(ownership, lambda row: (row["as_of"], row["person"]), "ownership")
    for row in ownership:
        verify_provenance(row, {"documented"})
        require(day(row["as_of"]) <= day(sources[row["source_id"]]["published_on"])
                and row["person"].strip() and int(row["beneficial_shares"]) >= 0
                and 0 <= Decimal(row["percent_reported"]) <= 100, "Invalid ownership row")
    timeline = rows(data / "timeline.csv", "id event_date disclosed_on precision status event claim_id")
    unique(timeline, lambda row: row["id"], "event")
    for row in timeline:
        eid = row["id"]
        require(re.fullmatch(r"EV-\d{3,}", eid) and row["event"].strip(), f"{eid}: invalid event")
        verify_provenance(row, {"documented", "attributed", "scheduled"})
        require(row["status"] == claims[row["claim_id"]]["status"], f"{eid}: conflicting evidence status")
        pattern = DATE_PATTERNS.get(row["precision"])
        value = row["event_date"]
        require(pattern and re.fullmatch(pattern, value), f"{eid}: date precision mismatch")
        dated(value)
        if row["status"] != "scheduled":
            require(value <= snapshot["as_of"][:len(value)], f"{eid}: future event treated as fact")
        if disclosed := row["disclosed_on"]:
            require(day(disclosed) <= cutoff, f"{eid}: unpublished disclosure")
            if row["status"] != "scheduled":
                require(disclosed[:len(value)] >= value, f"{eid}: disclosure predates event")
    market = rows(data / "market_observations.csv", "symbol trade_date close_usd claim_id source_id")
    unique(market, lambda row: (row["symbol"], row["trade_date"]), "market observation")
    for row in market:
        verify_provenance(row, {"derived"})
        close = Decimal(row["close_usd"])
        require(row["symbol"].isalpha() and row["symbol"].isupper()
                and close.is_finite() and close > 0 and day(row["trade_date"]) <= cutoff
                and sources[row["source_id"]]["kind"] == "market_data", "Invalid market observation")
    return snapshot, sources, claims, annual, quarterly, timeline, market


def price_return(start, end):
    return (Decimal(end) / Decimal(start) - 1) * 100


def market_returns(market):
    prices = {(row["symbol"], row["trade_date"]): row["close_usd"] for row in market}
    start, pre, post = "2026-11-06", "2026-11-20", "2026-11-23"
    return {symbol: [price_return(prices[symbol, start], prices[symbol, pre]),
                     price_return(prices[symbol, pre], prices[symbol, post]),
                     price_return(prices[symbol, start], prices[symbol, post])]
            for symbol in ("NVDA", "SPY", "SOXX")}


def financial_summary(annual):
    ordered = sorted(annual, key=lambda row: int(row["fiscal_year"]))
    first, last = ordered[0], ordered[-1]
    years = int(last["fiscal_year"]) - int(first["fiscal_year"])
    total_first, total_last = (Decimal(row["revenue_usd_m"]) for row in (first, last))
    dc_first, dc_last = (Decimal(row["data_center_usd_m"]) for row in (first, last))
    return {
        "total_cagr": ((total_last / total_first) ** (Decimal(1) / years) - 1) * 100,
        "dc_cagr": None if dc_first == 0 else ((dc_last / dc_first) ** (Decimal(1) / years) - 1) * 100,
        "growth_contribution": None if total_first == total_last else
            (dc_last - dc_first) / (total_last - total_first) * 100,
    }


def source_link(sid, sources):
    return f"[{sid}](<{sources[sid]['url']}>)"


def render(root=ROOT):
    snapshot, sources, claims, annual, quarterly, timeline, market = validate(root)
    note = f"Evidence reviewed through **{snapshot['as_of']}**. Generated by `scripts/research.py`."
    ledger = ["# Evidence ledger", "", note, "", "See the [source registry](registry.csv).", ""]
    for cid, claim in sorted(claims.items()):
        ledger.extend([f"## {cid}", "", f"**{claim['status'].capitalize()}** · Reviewed {claim['reviewed_on']}",
                       "", claim["statement"], "", f"**Evidence boundary.** {claim['boundary']}", ""])
        for item in claim["evidence"]:
            sid = item["source_id"]
            source = sources[sid]
            published = source["published_on"] or "publication date unavailable"
            ledger.append(f"- {source_link(sid, sources)} · {source['publisher']} · {published} · {item['locator']}")
        ledger.append("")
    events = ["# Research timeline", "", note, "",
              "| Event date | Disclosure | Status | Event | Evidence |",
              "|---|---|---|---|---|"]
    for row in sorted(timeline, key=lambda item: (item["event_date"], item["id"])):
        cid = row["claim_id"]
        events.append(f"| {row['event_date']} | {row['disclosed_on'] or '—'} | {row['status']} | "
                      f"{row['event']} | [{cid}](../sources/evidence.md#{cid.lower()}) |")
    tables = ["# Reproducible metrics", "", note, "",
              "## Annual NVIDIA financials", "",
              "Amounts are USD millions. Data Center is an end market. See [CLM-009](../sources/evidence.md#clm-009).", "",
              "| Fiscal year | Revenue | Data Center | GAAP R&D | Data Center share | R&D intensity |",
              "|---|---:|---:|---:|---:|---:|"]
    for row in sorted(annual, key=lambda item: int(item["fiscal_year"])):
        revenue, dc, rd = (int(row[key]) for key in ("revenue_usd_m", "data_center_usd_m", "gaap_rd_usd_m"))
        tables.append(f"| FY{row['fiscal_year']} | {revenue:,} | {dc:,} | {rd:,} | {100*dc/revenue:.2f}% | {100*rd/revenue:.2f}% |")
    summary = financial_summary(annual)
    formatted = {name: "undefined" if value is None else f"{value:.2f}%"
                 for name, value in summary.items()}
    tables.extend(["", f"Endpoint CAGR was **{formatted['total_cagr']}** for total revenue and "
                   f"**{formatted['dc_cagr']}** for Data Center. Data Center accounted for "
                   f"**{formatted['growth_contribution']}** of the net revenue change.", "", "## Quarterly results", "",
                   "Amounts are USD millions. Data Center is rounded as reported. See [CLM-010](../sources/evidence.md#clm-010).", "",
                   "| Fiscal quarter | End date | Revenue | Data Center | GAAP R&D |",
                   "|---|---|---:|---:|---:|"])
    for row in sorted(quarterly, key=lambda item: (int(item["fiscal_year"]), int(item["quarter"]))):
        tables.append(f"| Q{row['quarter']} FY{row['fiscal_year']} | {row['period_end']} | "
                      f"{int(row['revenue_usd_m']):,} | ~{int(row['data_center_usd_m_rounded']):,} | "
                      f"{int(row['gaap_rd_usd_m']):,} |")
    returns = market_returns(market)
    tables.extend(["", "## November 2026 market observations", "",
                   "Close-to-close USD price returns. See [CLM-019](../sources/evidence.md#clm-019).", "",
                   "| Symbol | Nov 6–20 | Nov 20–23 | Nov 6–23 |",
                   "|---|---:|---:|---:|"])
    for symbol, changes in returns.items():
        tables.append(f"| {symbol} | " + " | ".join(f"{change:+.2f}%" for change in changes) + " |")
    gap = returns["NVDA"][1] - returns["SOXX"][1]
    tables.extend(["", f"The November 20–23 NVDA–SOXX difference was **{gap:+.2f} percentage points**.",
                   "This comparison is descriptive."])
    return {"sources/evidence.md": ledger, "docs/timeline.md": events, "docs/metrics.md": tables}


def check_links(root=ROOT):
    root = root.resolve()
    checked = 0
    for path in root.rglob("*.md"):
        if ".git" in path.parts:
            continue
        for target in LINK.findall(path.read_text(encoding="utf-8")):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme:
                require(valid_https(target.strip("<>")), f"{path.name}: invalid URL {target}")
                continue
            if parsed.netloc:
                raise ValueError(f"{path.name}: invalid relative link {target}")
            dest = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            require(dest.is_relative_to(root) and dest.exists(), f"{path.name}: broken link {target}")
            if parsed.fragment and dest.suffix == ".md":
                headings = re.findall(r"^#+ (.+)$", dest.read_text(encoding="utf-8"), re.MULTILINE)
                anchors = {re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-") for heading in headings}
                require(unquote(parsed.fragment) in anchors, f"{path.name}: missing heading for {target}")
            checked += 1
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    for name, lines in render().items():
        path = ROOT / name
        result = "\n".join(lines).rstrip() + "\n"
        if args.mode == "build":
            path.write_text(result, encoding="utf-8")
        else:
            require(path.is_file() and path.read_text(encoding="utf-8") == result,
                    f"{name} is stale. Run python3 scripts/research.py build.")
    print(f"Evidence and data valid. Checked {check_links()} local links.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, ArithmeticError, OSError) as error:
        raise SystemExit(str(error)) from error
