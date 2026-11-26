# Datasets and provenance

CSV files are UTF-8 with a header and one observation per row. Original document and statement locators are in the [evidence ledger](../sources/evidence.md), joined through `claim_id`. Fields ending in `source_id` resolve to specific records in the [source registry](../sources/registry.csv). The registry includes public dates and stable filing accessions where applicable.

| Dataset | Row grain and interpretation |
|---|---|
| [Annual financials](annual_financials.csv) | One NVIDIA fiscal year. Consolidated revenue, Data Center market revenue and consolidated GAAP R&D expense in USD millions. |
| [Quarterly financials](quarterly_financials.csv) | One NVIDIA fiscal quarter with period end and disclosure date. `source_id` points to the earnings filing or exhibit. `market_source_id` points to the issuer’s original quarterly market table. Amounts are USD millions as published. |
| [Ownership](ownership.csv) | One person and measurement date from a definitive proxy. Beneficial shares and reported percentage, as disclosed. |
| [Timeline](timeline.csv) | One historical or scheduled event with category, precision, status, disclosure date where known and its closest primary source. |
| [Market observations](market_observations.csv) | One selected symbol and U.S. trade date. Closing USD observations independently transcribed for three comparison dates. Consult the vendor for broader data and its applicable terms. |
| [Chip policy](policy_tracker.csv) | One published rule, announcement, issuer disclosure or public oversight action. Empty date fields reflect the available record. `next_on` is the scheduled occurrence, comment deadline or rescission date shown in the record. |
| [Archive index](archive_index.csv) | One indexed interview, transcript record or publisher-provided chapter. `event_date` is the recording, event or publication date described in the entry. `timestamp_seconds` locates a video chapter. |
| [Technical milestones](technology_milestones.csv) | One selected dated moment in accelerator programming, research or product development. Joins to the chronology via `event_id`. |
| [Benchmark case](benchmark_comparison.csv) | One selected published MLPerf Inference system result. `upstream_locator` identifies the original row and attribution. |

See the [quarterly methodology](../docs/quarterly-financial-panel.md), [policy update practice](../docs/chip-policy-tracker.md) and [benchmark comparison](../docs/oral-history-and-cuda.md). The [derived metrics](../docs/metrics.md) and [browser snapshot](../observatory/data.js) can be rebuilt offline. The [license](../LICENSE) applies to original project contributions.
