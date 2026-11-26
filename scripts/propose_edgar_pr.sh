#!/usr/bin/env bash
set -euo pipefail

queue=watch/edgar-candidates.csv
if git diff --quiet -- "$queue"; then
    exit 0
fi

in_progress=$(gh pr list --repo "$GITHUB_REPOSITORY" --state open --base "$BASE_BRANCH" \
    --limit 100 --json headRefName,isCrossRepository \
    --jq 'any(.[]; (.headRefName | startswith("bot/edgar/")) and .isCrossRepository == false)')
if [[ "$in_progress" == true ]]; then
    echo "A draft is awaiting review. New filings will be collected again after it closes."
    exit 0
fi

gh auth setup-git --hostname github.com
git add -- "$queue"
if [[ "$(git diff --cached --name-only)" != "$queue" ]]; then
    echo "Unexpected staged changes" >&2
    exit 1
fi
tree=$(git write-tree)
parent=$(git rev-parse HEAD)
branch="bot/edgar/${parent:0:12}-${tree:0:12}"

# Reuse a branch if a previous run pushed it but could not open the PR.
remote_ref=$(git ls-remote origin "refs/heads/$branch")
if [[ -n "$remote_ref" ]]; then
    git fetch --no-tags origin "refs/heads/$branch"
    if [[ "$(git rev-parse FETCH_HEAD^{tree})" != "$tree" || "$(git rev-parse FETCH_HEAD^)" != "$parent" ]]; then
        echo "Unexpected existing automation branch: $branch" >&2
        exit 1
    fi
else
    git -c user.name='github-actions[bot]' \
        -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
        commit -m "Queue EDGAR filing metadata for review"
    git push origin "HEAD:refs/heads/$branch"
fi

gh pr create --repo "$GITHUB_REPOSITORY" --base "$BASE_BRANCH" --head "$branch" --draft \
    --title "Review new NVIDIA EDGAR filings" --body-file .github/edgar-draft-body.md
