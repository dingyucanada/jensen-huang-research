# Research methodology

## From a source to a published claim

Start with a precise proposition and the date it applies to. Locate a primary source with direct authority for that proposition, then record the publisher, date, access date, stable reference and location. Compare independent reporting for material disputes and record which details are independently observed. The same issuer statement in an exhibit and a newsroom post has one origin.

Issuer filings directly establish what was disclosed. Government pages directly establish what an agency issued or a committee announced. An assertion inside either record still requires evidence relevant to that assertion. Use court findings, agency determinations or independently corroborated primary material to assess serious wrongdoing. Record the stage of any procedure and the response to an allegation when material. Hold sensitive or weakly sourced material out of public issues and public editorial queues.

| Label | Meaning |
|---|---|
| Documented | A record directly supports the stated action or measured observation |
| Attributed | A named party said or reported something within its scope |
| Scheduled | An authorized calendar or announcement lists a future or pending event |
| Derived | A documented calculation uses identified observations |
| Interpretation | An analytical inference or explicit hypothesis |
| Unverified | Evidence is insufficient. Reserve a public ledger entry for a neutral, useful omission with no sensitive details |

## Dates and revisions

The snapshot cutoff is in [snapshot.json](../snapshot.json). Source publication, access, claim review, event and public disclosure dates have distinct meanings. Date-only governance events use the date stated in the source. Omit a publication or disclosure date when the record fails to establish one. Use explicit year or month precision for historical events. Update the review date when re-checking a claim and advance the snapshot only after the editorial briefing and relevant dated records are reviewed.

Stable source, claim and event identifiers remain fixed once published. Attach revised evidence to the existing ID when correcting the same proposition. Use a new ID for a distinct proposition. Explain the change in the [changelog](../CHANGELOG.md) and preserve previous versions in Git history. Form an internal record of contested edits before publishing any sensitive detail.

## Analytical conventions

- Share and intensity divide the selected amount by consolidated revenue for the same period.
- CAGR uses the number of fiscal years between endpoints. Data Center contribution to growth divides its change by the consolidated revenue change.
- Close-to-close price returns use `100 × (ending close / beginning close − 1)`. Benchmark differences subtract returns and are expressed in percentage points.
- For qualitative coding, fix the corpus and codebook, use two independent coders, report disagreements, and keep a dated source location for each observation.

Automated checks test repository structure, reference consistency and calculations. They cannot determine whether a source actually supports an interpretation. The maintenance cadence is daily candidate intake on weekdays, weekly editorial and link review, quarterly financial updates, and a review after material board or government disclosures.
