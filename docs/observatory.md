# NVIDIA Evidence Observatory

The observatory is the browser interface for the Jensen Huang Research Project. It reads a checked snapshot of the repository’s data and includes direct links to the published evidence. The same release contains the [source ledger](../sources/evidence.md) and [research methodology](methodology.md).

## Open and share

Open [observatory/index.html](../observatory/index.html) from a local checkout or an extracted release archive. The interface, filters, charts and downloads work locally. Opening an original source requires network access. The browser interface also runs from an ordinary static host.

- The timeline sorts and filters records. Expand a record to see evidence status, disclosures and the original source. Download filtered CSV rows or export the November governance comparison as PNG.
- The financial dashboard includes three trends, a quarter inspector, EDGAR accession links, the original Data Center tables and reusable CSV and PNG exports.
- The chip policy tracker distinguishes publication, effective date, follow-up deadline, announced schedule and documented investigative action.
- The archive includes original interview links, publisher timestamps, technical milestones and a worked comparison of two MLPerf Inference submissions.

Record permalinks preserve an event or policy ID. On a hosted copy, a link such as `#timeline?event=EV-014` can be shared directly. A local file copies the record path without exposing the local filesystem path. Append that record path to the hosted URL.

## Rebuild after editing evidence

```sh
python3 scripts/research.py build
python3 scripts/observatory.py build
python3 scripts/research.py check
python3 scripts/observatory.py check
python3 -m unittest discover -s tests -v
```

The browser uses `observatory/data.js`, a generated snapshot of the CSV and JSON inputs. Review diffs in the source datasets and refresh the generated file. Exported presentation PNGs carry the snapshot date and provenance. The app depends only on files in the `observatory` directory.

## Optional browser verification

If Playwright for Python and its Chromium browser are installed, run `python3 tests/browser_smoke.py`. It exercises the offline file directly. Pass `--artifacts path` to retain desktop and mobile screenshots and check the downloaded PNG and CSV artifacts. Standard tests and the build require only Python.

## GitHub Pages

After editorial review and merge to the default branch, choose **GitHub Actions** as the publishing source under **Settings → Pages** and set the repository variable `ENABLE_RESEARCH_PAGES` to `true`. Run **Publish reviewed research pages** from the default branch. Subsequent reviewed changes under the portal directory trigger a deployment. The workflow validates the dataset and copies only the static portal directory.

Published records retain the declared review cutoff. Future dates stay scheduled until official records establish a change or occurrence. Keep the [dated briefing](brief-2026-11-26.md) as a versioned record.
