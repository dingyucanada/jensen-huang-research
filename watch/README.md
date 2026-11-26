# Editorial intake

The weekday EDGAR watch checks NVIDIA's public SEC submissions feed for selected current reports, annual reports, quarterly reports and proxy filings. It collects constrained filing metadata for CIK 1045810. Public filings already linked in the registry are recognized by accession. The collection start is in [settings.json](settings.json).

## Review steps

The [proposed intake](edgar-candidates.csv) is an editorial queue. The workflow creates at most one open same-repository intake draft at a time. A reviewer can turn the draft into a ready pull request after inspecting the diff and approving the check run if GitHub prompts for approval. Merge the metadata queue after review. Resolve pending entries in a separate editorial change by adding the relevant accession to the registry or recording a reason in [dispositions.csv](dispositions.csv). Run the collector again to refresh the queue. Unresolved entries persist across feed refreshes.

Open the original filing, locate the exact passage and verify timing, scope and relevance. Independently check material disputes and update source and claim records through an editorial pull request. House and Senate notices, BIS rule changes and NVIDIA announcements still require manual editorial review. Use the [dated briefing](../docs/brief-2026-11-26.md) as the first review checklist.

## Setup after repository ownership is confirmed

1. Protect the default branch and require a human review plus the **Evidence, links and tests** check. Disable auto-merge for intake.
2. Set the repository Actions variable `SEC_CONTACT` to a project email address for the SEC request header.
3. Enable GitHub Actions to create pull requests and set the repository Actions variable `ENABLE_EDGAR_WATCH` to `true`. The workflow uses the built-in repository token.
4. Run **Propose EDGAR updates** from the default branch. Approve checks for an Actions-created PR when prompted. Review the first result and confirm the only changed path is `watch/edgar-candidates.csv`.

The watcher accepts only scheduled and manual runs on the default branch. It proposes an isolated branch with a draft pull request, and has no merge step. If a request fails, the job fails and keeps the prior queue. An unchanged queue produces no pull request. If the push succeeds and PR creation fails, a rerun from the same base can reuse the matching automation branch. The branch namespace `bot/edgar/` is reserved for this workflow.

On a machine with network access, run `SEC_CONTACT=research@example.org python3 scripts/edgar_watch.py` using your actual project contact. For an offline trial, pass `--fixture tests/fixtures/edgar.json --date 2026-11-30 --output /tmp/edgar-candidates.csv`. Fixture filings are synthetic.

Scheduled source reachability runs separately. They fail on confirmed 404 or 410 responses and report blocked, throttled or unavailable hosts for editorial review. GitHub may pause schedules on inactive public repositories. [SEC data API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) · [GitHub workflow token](https://docs.github.com/en/actions/concepts/security/github_token) · [GitHub scheduling](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
