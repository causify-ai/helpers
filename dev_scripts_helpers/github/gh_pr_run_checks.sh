#!/bin/bash -e
#
# """
# Print the CI check state of a PR, rerun its checks, then print the state
# again so the before/after is visible in one shot.
#
# Rerun everything for the PR of the current branch:
# > gh_pr_run_checks.sh
#
# Rerun only the failed jobs of each run, keeping passed jobs untouched:
# > gh_pr_run_checks.sh -f
#
# Target a specific PR instead of the current branch's PR:
# > gh_pr_run_checks.sh -p 123
#
# List the runs that would be rerun without rerunning them:
# > gh_pr_run_checks.sh -n
# """

#set -x

# Initialize default values.
failed_only=0
dry_run=0
pr_number=""

# Function to show usage.
show_usage() {
    # """
    # Print the command-line usage to stdout.
    # """
    echo "Usage: $0 [-f] [-n] [-p pr_number]"
    echo "  -f            Rerun only the failed jobs of each run (default: rerun all jobs)"
    echo "  -n            Dry run: list the runs that would be rerun, don't rerun them"
    echo "  -p pr_number  PR to target (default: PR for the current branch)"
}

# Parse command-line options.
while getopts 'fnp:h' flag; do
    case "${flag}" in
        f) failed_only=1 ;;
        n) dry_run=1 ;;
        p) pr_number="${OPTARG}" ;;
        h) show_usage
           exit 0 ;;
        *) show_usage
           exit 1 ;;
    esac
done

# `gh run list` needs a branch, not a PR number, so resolve the PR's head
# branch either from the given PR or from the PR open on the current branch.
if [[ -z "$pr_number" ]]; then
    pr_number=$(gh pr view --json number -q .number)
    branch=$(gh pr view --json headRefName -q .headRefName)
else
    branch=$(gh pr view "$pr_number" --json headRefName -q .headRefName)
fi
echo "# PR #$pr_number (branch '$branch')"

echo "# Checks state (before)"
gh pr checks "$pr_number" || true

# Only completed runs can be rerun: `gh run rerun` errors out on a run that
# is still queued or in progress, so filter those out.
run_ids=$(gh run list --branch "$branch" --json databaseId,status \
    -q '.[] | select(.status == "completed") | .databaseId')

if [[ -z "$run_ids" ]]; then
    echo "# No completed runs to rerun"
    exit 0
fi

echo "# Rerunning checks"
for run_id in $run_ids; do
    if [[ $dry_run -eq 1 ]]; then
        echo "Would rerun run $run_id"
        continue
    fi
    if [[ $failed_only -eq 1 ]]; then
        gh run rerun "$run_id" --failed || echo "Failed to rerun $run_id"
    else
        gh run rerun "$run_id" || echo "Failed to rerun $run_id"
    fi
done

if [[ $dry_run -eq 1 ]]; then
    exit 0
fi

# Give GitHub a few seconds to register the new runs before checking again,
# otherwise the "after" state below still shows the old (completed) runs.
sleep 5

echo "# Checks state (after)"
gh pr checks "$pr_number" || true
