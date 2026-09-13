#!/bin/bash
# """
# Print the GitHub info for the current branch: the number, title, and URL of
# the PR and of the issue it closes (if any).
# """

set -eu

# Get the PR info for the current branch.
PR_JSON=$(gh pr view --json number,title,url,closingIssuesReferences)

PR_NUMBER=$(echo "$PR_JSON" | jq -r '.number')
PR_TITLE=$(echo "$PR_JSON" | jq -r '.title')
PR_URL=$(echo "$PR_JSON" | jq -r '.url')

# Get the number of the first issue closed by the PR, if any.
ISSUE_NUMBER=$(echo "$PR_JSON" | jq -r '.closingIssuesReferences[0].number // empty')

if [ -n "$ISSUE_NUMBER" ]; then
    # Get the issue info.
    ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --json number,title,url)
    ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
    ISSUE_URL=$(echo "$ISSUE_JSON" | jq -r '.url')
    echo "Issue number: $ISSUE_NUMBER"
    echo "Issue title: $ISSUE_TITLE"
    echo "Issue url: $ISSUE_URL"
else
    echo "Issue number: -"
    echo "Issue title: -"
    echo "Issue url: -"
fi

echo "PR number: $PR_NUMBER"
echo "PR title: $PR_TITLE"
echo "PR url: $PR_URL"
