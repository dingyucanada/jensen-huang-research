# Jensen Huang Research Project

An independent research repository on Jensen Huang, NVIDIA, and the institutions shaping AI infrastructure. Trace who did what, when it became public, and which source supports each claim.

**Evidence reviewed through November 26, 2026 · v0.2.0**

[Observatory guide](docs/observatory.md) · [Governance timeline](docs/timeline.md) · [Evidence ledger](sources/evidence.md) · [Reproducible metrics](docs/metrics.md) · [Latest briefing](docs/brief-2026-11-26.md)

| Question | What the record shows |
|---|---|
| When did NVIDIA's CEO change? | EDGAR records Huang's resignation as effective November 11 and reinstatement as effective November 22, 2026. The filings were public the following day in each case. [Departure](sources/evidence.md#clm-001) · [Return](sources/evidence.md#clm-002) |
| How much of NVIDIA's revenue comes from Data Center? | **89.72% in FY2026**, calculated from $193.737B in Data Center end-market revenue and $215.938B in consolidated revenue. [Annual financials](docs/metrics.md#annual-nvidia-financials) |
| What is the next public record to watch? | A House committee announcement listed December 1 and 2 transcribed interviews. The Senate Banking Committee listed Huang for a December 3 public hearing. [House](sources/evidence.md#clm-005) · [Senate](sources/evidence.md#clm-006) |

## Explore the data and archives

The [NVIDIA Evidence Observatory](docs/observatory.md) includes a searchable timeline, 27 quarterly financial observations, a chip policy tracker, timestamped interviews and an MLPerf worked comparison. Open `observatory/index.html` after cloning or extracting the repository. No browser setup or network connection is needed for filters and charts.

[Quarterly financial panel](docs/quarterly-financial-panel.md) · [Policy tracker](docs/chip-policy-tracker.md) · [Oral history and CUDA archive](docs/oral-history-and-cuda.md)

## Read the research

1. [Research question and framework](research/01-framework.md)
2. [Biography and documented leadership practice](research/02-leadership.md)
3. [Founder authority and corporate governance](research/03-governance.md)
4. [CUDA and the economics of technical infrastructure](research/04-technology.md)
5. [Export controls and semiconductor policy](research/05-policy.md)
6. [The November 2026 leadership transition](research/06-november-2026.md)
7. [Financial evidence and market comparisons](research/07-empirical.md)
8. [Findings, rival explanations and research agenda](research/08-research-agenda.md)

## Reproduce the tables and check the evidence

Run from the project root with Python 3.9 or newer. The build uses the bundled CSV and JSON files and the Python standard library.

```sh
python3 scripts/research.py build
python3 scripts/observatory.py build
python3 scripts/research.py check
python3 scripts/observatory.py check
python3 -m unittest discover -s tests -v
```

The [data dictionary](data/README.md) describes the inputs and units. The [methodology](docs/methodology.md) defines the evidence labels and explains how to correct a claim. The [editorial watch](watch/README.md) stages SEC filing metadata for review through draft pull requests.

## Contribute or cite

[Contributing](CONTRIBUTING.md) · [Citation metadata](CITATION.cff) · [Changelog](CHANGELOG.md) · [License scope](LICENSE)

This project has no affiliation with NVIDIA or Jensen Huang.
