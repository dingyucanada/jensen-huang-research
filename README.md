# Jensen Huang Research Project

**Two SEC filings place Jensen Huang’s resignation and reinstatement 11 days apart.** Across 27 fiscal quarters, Data Center’s share of NVIDIA revenue grew from 37.05% to 92.89%. The NVIDIA Evidence Observatory connects those findings, U.S. chip rules, and CUDA’s history to records you can check yourself. [Governance timeline](docs/timeline.md) · [Quarterly sources](docs/quarterly-financial-panel.md)

**Evidence reviewed through November 26, 2026** · 41 timeline events · 27 fiscal quarters · 18 policy records · 17 archive entries

[**Browse the source collection**](#featured-source-collection) · [**Download the interactive observatory**](https://github.com/dingyucanada/jensen-huang-research/releases/download/v0.2.0/jensen-huang-research-v0.2.0.zip) · [Read the November briefing](docs/brief-2026-11-26.md)

Extract the ZIP and open `observatory/index.html`. Search, chart inspection, and CSV and PNG exports work offline. [Observatory guide](docs/observatory.md)

## The November leadership transition

[![Governance timeline. Resignation effective November 11 and disclosed November 12. Reinstatement effective November 22 and disclosed November 23.](docs/assets/nvidia-governance-dates.png)](research/06-november-2026.md)

NVIDIA’s board accepted Huang’s resignation **effective November 11** and named Colette Kress interim CEO. It reinstated Huang **effective November 22**. Each action was disclosed the following day. The same public record describes an inquiry that NVIDIA said would continue. [Departure filing](sources/evidence.md#clm-001) · [Reinstatement filing](sources/evidence.md#clm-002) · [Inquiry status](sources/evidence.md#clm-003)

[Read the 41-event timeline](docs/timeline.md) · [Get the timeline CSV](data/timeline.csv)

## Where does NVIDIA’s revenue come from?

In **FY2027 Q3**, which ended October 25, 2026, NVIDIA reported **$115.844B** of revenue. Data Center accounted for **$107.610B**, or **92.89%**. GAAP R&D reached **$7.454B**, or **6.43%** of revenue. At the start of the series, R&D was **$0.735B** and **23.86%** of revenue. [Figures, source tables and definitions](docs/quarterly-financial-panel.md)

[![Three charts for 27 quarters. Consolidated revenue and Data Center share rise, while GAAP R&D as a share of revenue ends below its starting level.](docs/assets/nvidia-quarterly-trends.png)](docs/quarterly-financial-panel.md)

[Get quarterly CSV](data/quarterly_financials.csv) · [Get annual CSV](data/annual_financials.csv) · [Reproduce the metrics](docs/metrics.md)

## What should readers watch in chip policy?

- **Rules and deadlines.** The BIS remote-access rule took effect November 19, with comments due January 19, 2027. A separate Entity List amendment was published November 25 and took effect November 23. [Remote-access rule](sources/evidence.md#clm-041) · [Entity List amendment](sources/evidence.md#clm-044)
- **Congressional calendar.** At the November 26 cutoff, House committees listed transcribed interviews for Huang on December 1 and NVIDIA General Counsel Tim Teter on December 2. The Senate Banking Committee listed Huang for a December 3 public hearing. [House notice](sources/evidence.md#clm-005) · [Senate calendar](sources/evidence.md#clm-006)

[Read the policy tracker](docs/chip-policy-tracker.md) · [Get the policy CSV](data/policy_tracker.csv)

## How did CUDA become infrastructure?

Start with Huang’s Computer History Museum oral history or his 2009 Stanford talk. Follow the archive to the original CUDA and AlexNet papers, timestamped interview chapters, and 11 technical milestones. [Oral history and CUDA guide](docs/oral-history-and-cuda.md) · [Interview index CSV](data/archive_index.csv) · [Technical milestones CSV](data/technology_milestones.csv)

**Try the MLPerf comparison.** In two eight-accelerator Dell systems running the same Llama 2 70B workload, the B300 system delivered **8.97%** higher Offline throughput and **2.85%** higher Server throughput relative to the MI355X system. The two submissions use different software stacks. The comparison is specific to those configurations and scenarios. [Compare the four results](data/benchmark_comparison.csv) · [Pinned source data and rules](sources/evidence.md#clm-040)

## Featured source collection

Start with an original filing, rule, recording, paper, or dataset. The evidence ledger connects each record to the claims it supports. [Full evidence ledger](sources/evidence.md) · [Source registry CSV](sources/registry.csv) · [Data catalog](data/README.md)

### Governance and ownership

- **Board actions.** Read Item 5.02 in each 8-K for the effective dates of both decisions and the interim leadership appointment. [Resignation 8-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000082/nvda-20261111.htm) · [Reinstatement 8-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000090/nvda-20261122.htm)
- **Ownership and board independence.** Find Huang’s reported beneficial ownership and NVIDIA’s description of director independence in the 2026 proxy. [Definitive proxy statement](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000036/nvda-20260512.htm) · [Ownership table and locator](sources/evidence.md#clm-008)

### Financial statements and market data

- **FY2027 Q3 source pair.** Open the consolidated income statement for revenue and GAAP R&D, then the issuer’s market table for the Data Center amount and its recast note. [SEC earnings exhibit](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000088/q3fy27pr.htm) · [Revenue by Market Platform PDF](https://s201.q4cdn.com/141608511/files/doc_financials/2027/Q327/Rev-by-Mkt-Qtrly-Trend-Q327.pdf)
- **Long-run series.** Follow the source IDs in each quarterly row to the filing and market table behind the numbers. [Quarterly data](data/quarterly_financials.csv) · [Source map and audit instructions](docs/quarterly-financial-panel.md)

### Chip policy and oversight

- **Rule text.** Find both effective dates and the remote-access rule’s comment deadline in the Federal Register’s *Dates* sections. [Remote-access rule](https://www.govinfo.gov/content/pkg/FR-2026-11-19/html/2026-23529.htm) · [Entity List amendment](https://www.federalregister.gov/documents/2026/11/25/2026-23999/additions-to-the-entity-list)
- **Official calendars.** The House notice names participants and interview dates. The Senate hearing page lists the witness and provides the public webcast entry. [House committee notice](https://intelligence.house.gov/2026/11/17/jensen-huang-and-nvidia-agree-to-appear-before-congress/) · [Senate hearing page](https://www.banking.senate.gov/hearings/protecting-americas-ai-advantage-oversight-of-us-export-controls)

### Founder interviews and oral history

- **NVIDIA’s early years.** Compare Huang’s account of the first six months in his 2009 Stanford talk with his longer 2024 Computer History Museum oral history. [Stanford talk](https://stvp.stanford.edu/av/first-six-months-nvidia) · [Museum recording](https://www.youtube.com/watch?v=0c8i4T9BSqY) · [Timestamp index](data/archive_index.csv)

### CUDA papers and benchmarks

- **Programming model and workload.** Read the 2008 CUDA paper for the parallel programming model and the 2012 AlexNet paper for its GPU training setup. [CUDA paper](https://research.nvidia.com/publication/2008-03_scalable-parallel-programming-cuda) · [AlexNet paper](https://papers.nips.cc/paper_files/paper/2012/hash/c399862d3b9d6b76c8436e924a68c45b-Abstract.html)
- **Reproduce a comparison.** The pinned MLCommons results contain the original throughput rows for both Dell systems and both test scenarios. [MLCommons source CSV](https://github.com/mlcommons/inference_results_v6.1/blob/6623c6c8bac460c46a8768ac261bc0889c9c7f13/summary.csv) · [Four-row extract](data/benchmark_comparison.csv) · [Audit instructions](docs/oral-history-and-cuda.md#worked-mlperf-comparison)

## Eight research chapters

<details>
<summary>Browse all chapters</summary>

1. [Research question and framework](research/01-framework.md)
2. [Biography and documented leadership practice](research/02-leadership.md)
3. [Founder authority and corporate governance](research/03-governance.md)
4. [CUDA and the economics of technical infrastructure](research/04-technology.md)
5. [Export controls and semiconductor policy](research/05-policy.md)
6. [The November 2026 leadership transition](research/06-november-2026.md)
7. [Financial evidence and market comparisons](research/07-empirical.md)
8. [Findings, rival explanations and research agenda](research/08-research-agenda.md)

</details>

## Verify, reuse, and contribute

Each claim in the evidence ledger has a stable ID, a source, and a locator. Financial rows record both their filing and market-table sources. To rebuild the tables and browser data, run these commands from the project root with Python 3.9 or newer.

```sh
python3 scripts/research.py build
python3 scripts/observatory.py build
python3 scripts/research.py check
python3 scripts/observatory.py check
python3 -m unittest discover -s tests -v
```

The editorial watch can queue new SEC filings and Federal Register notices for human review through draft pull requests. To contribute, send an original source or a correction with a claim ID and a locator. [Data dictionary](data/README.md) · [Methodology](docs/methodology.md) · [Editorial watch](watch/README.md) · [Contribution guide](CONTRIBUTING.md)

[Release notes](https://github.com/dingyucanada/jensen-huang-research/releases/tag/v0.2.0) · [Citation metadata](CITATION.cff) · [Changelog](CHANGELOG.md) · [License scope](LICENSE)

An independent research project. No affiliation with NVIDIA or Jensen Huang.
