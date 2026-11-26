# Contributing

Reports of factual errors, stronger sources and reproducibility problems are welcome. Read the [methodology](docs/methodology.md) and [conduct guide](CODE_OF_CONDUCT.md) before opening an issue.

## Propose a correction

Use the [correction template](.github/ISSUE_TEMPLATE/correction.md). Include the claim or event ID, the relevant date, a primary URL and a locator. State what the source establishes and describe uncertainty or contradictory evidence. Keep personal information and unpublished allegations out of public issues. For sensitive corrections, ask a maintainer for a confidential channel using a general description.

## Submit a research change

1. Add or update source records in [registry.csv](sources/registry.csv). Preserve the IDs of existing sources.
2. Attach locators in [claims.json](sources/claims.json) and update linked data rows. Claim and event IDs stay stable across corrections.
3. Rebuild the indexes with `python3 scripts/research.py build`. Run `python3 scripts/research.py check` and `python3 -m unittest discover -s tests -v`.
4. Update the changelog for material changes. Add a dated briefing when advancing the review cutoff.
5. Open a pull request with the evidence, editorial reasoning, rights provenance and test results. An editorial reviewer must inspect material claims before merge.

By contributing original material, you agree to the applicable terms in [LICENSE](LICENSE). Cite third-party material and link to the source. Include redistributed material only when its authorization and scope are documented in the pull request.
