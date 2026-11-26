# Datasets and provenance

CSV files are UTF-8 with a header and one observation per row. Original document and statement locators are in the [evidence ledger](../sources/evidence.md), joined through `claim_id`. Where present, `source_id` identifies the specific record supplying the cell values. The [source registry](../sources/registry.csv) resolves IDs to URLs and access dates.

| Dataset | Row grain and interpretation |
|---|---|
| [Annual financials](annual_financials.csv) | One NVIDIA fiscal year. Consolidated total revenue, Data Center end-market revenue and consolidated GAAP R&D expense in USD millions. Use the GAAP statement for R&D because some filing tables use different definitions. |
| [Quarterly financials](quarterly_financials.csv) | One NVIDIA fiscal quarter. USD millions. The Data Center value is rounded to the nearest $100M as presented in the Q3 FY2027 earnings release. The filed statement supplies exact million-dollar total revenue and R&D. |
| [Ownership](ownership.csv) | One person and measurement date from a definitive proxy. Beneficial shares and reported percentage, as disclosed. |
| [Timeline](timeline.csv) | One historical or scheduled event with precision, status, disclosure date when known and evidence ID. |
| [Market observations](market_observations.csv) | One selected symbol and U.S. trade date. Closing USD observations independently transcribed for three comparison dates. Consult the vendor if you need a full series, adjustments or rights to reuse its material. |

Financials carry NVIDIA fiscal-year labels. Data Center is an end-market category. The derived [reports](../docs/metrics.md) can be rebuilt offline. The [license](../LICENSE) applies to original project contributions as stated there.
