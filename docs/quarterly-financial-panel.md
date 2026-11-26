# NVIDIA quarterly financial panel

The [quarterly dataset](../data/quarterly_financials.csv) covers **27 consecutive fiscal quarters from FY2021 Q1 through FY2027 Q3**. Revenue and GAAP R&D come from the three-month columns of NVIDIA’s filed earnings releases. The Data Center series uses the published quarterly market tables, including the latest Q3 FY2027 table for fiscal 2025 onward. Each row records the earnings disclosure date, the SEC accession via its source ID, and a separate ID for the original market table. [Q3 FY2027 market table and recast note](../sources/evidence.md#clm-042)

## What the data shows

- NVIDIA reported **$115.844B** of total revenue and **$107.610B** of Data Center revenue for the fiscal quarter ended October 25, 2026. The resulting Data Center share was **92.89%**. The corresponding FY2021 Q1 figures were **$3.080B**, **$1.141B** and **37.05%**. [FY2027 sources](../sources/evidence.md#clm-031) · [FY2021 sources](../sources/evidence.md#clm-025)
- GAAP R&D was **$7.454B** in FY2027 Q3, or **6.43%** of quarterly revenue. In FY2021 Q1 it was **$0.735B**, or **23.86%**. The ratio fell between these observations while nominal research expense rose. [Reproducible metrics](metrics.md#quarterly-results)

## Definitions and audit

All totals use the company’s fiscal calendar and USD millions as published. Data Center share is Data Center revenue divided by consolidated revenue. GAAP R&D intensity divides disclosed GAAP research and development expense by consolidated revenue. The three displayed trends use the same observation dates. The year label refers to the fiscal year, and Q3 FY2027 ended in calendar 2026.

The latest market presentation recast fiscal 2025 and later comparative periods. For continuity the panel uses top-level Data Center values. It does not splice in submarkets or operating segments and uses no inflation adjustment. Published quarterly R&D may differ by small rounding amounts from the annual total. The validator checks that each complete year reconciles within USD 2 million.

The release cross-checked the two consolidated GAAP amounts against NVIDIA’s SEC Company Facts for **26 quarters**. Fourth-quarter checks subtract nine-month facts from fiscal-year facts. FY2027 Q3 remains supported by the filed earnings exhibit and issued market table. Use the script with a separately obtained Company Facts response to replay the check. [SEC EDGAR API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) · [NVIDIA Company Facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json)

```sh
python3 scripts/verify_upstream.py --companyfacts /path/to/companyfacts.json
```

The evidence records link the original PDFs for [early quarters](../sources/evidence.md#clm-025), [transition quarters](../sources/evidence.md#clm-026), [FY2023–FY2024](../sources/evidence.md#clm-028) and [FY2025 onward](../sources/evidence.md#clm-042). With Poppler’s `pdftotext` available, verify the exact Data Center amounts and totals independently.

```sh
python3 scripts/verify_upstream.py --market-table SRC-040=/path/to/fy2022-q2-trend.pdf \
  --market-table SRC-041=/path/to/fy2024-q1-trend.pdf \
  --market-table SRC-042=/path/to/fy2024-q4-trend.pdf \
  --market-table SRC-043=/path/to/fy2027-q3-trend.pdf
```

Adding a quarter requires its end date, actual disclosure date, three amounts, filing accession and a market table with a locator. Keep actual and forecast rows distinct. A new market classification needs an explicit comparability note and the original issuer table.
