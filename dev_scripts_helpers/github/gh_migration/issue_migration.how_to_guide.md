<!-- toc -->

- [Issue Migration Guide](#issue-migration-guide)
- [Overview](#overview)
  * [What It Does](#what-it-does)
- [Requirements](#requirements)
  * [Directory Layout](#directory-layout)
- [Quick Start](#quick-start)
  * [Set Up](#set-up)
  * [Dry-Run (Preview Only)](#dry-run-preview-only)
  * [Execute for Real](#execute-for-real)
  * [Script Flags & Behavior](#script-flags--behavior)
  * [Input File Rules](#input-file-rules)
  * [What Gets Transferred](#what-gets-transferred)
- [Examples](#examples)
  * [Migrate a Range (Closed Issues 1–50)](#migrate-a-range-closed-issues-1%E2%80%9350)
  * [Migrate Specific Single Issues Regardless of State](#migrate-specific-single-issues-regardless-of-state)
  * [Generate a Closed-Issues List Up to #400 (Optional Helper)](#generate-a-closed-issues-list-up-to-%23400-optional-helper)
  * [What Transfers & What Doesn’T (Github Behavior)](#what-transfers--what-doesnt-github-behavior)
- [Troubleshooting](#troubleshooting)
- [Idempotency & Safety](#idempotency--safety)
  * [Exit Codes](#exit-codes)
- [Maintenance Notes (For Developers)](#maintenance-notes-for-developers)
  * [High-Level Algorithm](#high-level-algorithm)
  * [Known Limitations](#known-limitations)
- [Appendix: Common Command Snippets](#appendix-common-command-snippets)

<!-- tocstop -->

# Issue Migration Guide

# Overview

Bulk-transfer issues from one repository to another using a **Python** script
that talks to GitHub’s GraphQL API.

- **Script**: `.github/gh_migration/bulk_transfer_issues.py`
- **Input list**: `.github/gh_migration/issues_to_transfer.txt`

## What It Does

- Accepts **ranges and single IDs** (e.g., `1-10 20-400`) from a text file
- **Validates in the source repo only** (no cross-repo bleed)
- Transfers **issues** (PRs are automatically excluded)
- Respects a **state filter** (`open` / `closed` / `all`)
- Logs **titles**, **reasons for skips**, and (optionally) **redirects** for
  already-transferred issues
- Supports **dry-run** previews

> GitHub assigns new numbers in the destination repo. If an issue is already
> moved, logs will indicate it (and, with `--trace-redirect`, show the
> destination URL).

# Requirements

* **Github Token** with Access to Source & Destination Repos (Export One):

  ```bash
  export GITHUB_TOKEN=ghp_your_token_here
  # or: export GH_TOKEN=ghp_your_token_here
  ```

## Directory Layout

```text
.github/
  gh_migration/
    bulk_transfer_issues.py
    issues_to_transfer.txt
```

Example `issues_to_transfer.txt`:

```text
# You Can Mix Ranges and Single Numbers; Commas or Spaces Both Work.
# Words Like "closed" in a Line Are Ignored; the Script Uses --State.
closed 1-10, 12-20
# Additional Singles:
33
34
# Comments Are OK
```

# Quick Start

## Set Up

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

## Dry-Run (Preview Only)

```bash
python .github/gh_migration/bulk_transfer_issues.py \
  --src causify-ai/cmamp \
  --dst causify-ai/csfy \
  --file .github/gh_migration/issues_to_transfer.txt \
  --state closed \
  --dry-run \
  --why \
  --max-title 100 \
  --trace-redirect
```

This prints:

- **Plan** with the first N titles to transfer
- **Exclusions** with reasons (e.g., PR, wrong state, already transferred)
- A list of issues that **would** be transferred

## Execute for Real

```bash
python .github/gh_migration/bulk_transfer_issues.py \
  --src causify-ai/cmamp \
  --dst causify-ai/csfy \
  --file .github/gh_migration/issues_to_transfer.txt \
  --state closed \
  --sleep 2 \
  --why \
  --max-title 100
```

## Script Flags & Behavior

| Flag                        | Default                                       | Description                                                                  |
| --------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------- |
| `--src owner/repo`          | `causify-ai/cmamp`                            | Source repository.                                                           |
| `--dst owner/repo`          | `causify-ai/csfy`                             | Destination repository.                                                      |
| `--file path`               | `.github/gh_migration/issues_to_transfer.txt` | Input file with ranges/IDs.                                                  |
| `--state closed\|open\|all` | `closed`                                      | Filter by **source issue** state. Applies to **all IDs** (ranges & singles). |
| `--sleep N`                 | `2`                                           | Seconds to sleep between transfers (avoid rate limiting).                    |
| `--dry-run`                 | off                                           | Preview only; no changes made.                                               |
| `--why`                     | off                                           | Always print exclusion reasons (titles included when available).             |
| `--max-title N`             | `120`                                         | Truncate titles in logs (set `0` for no truncation).                         |
| `--trace-redirect`          | off                                           | Show final URL if a source number was already transferred (browser-style).   |

**Note:** If you want to migrate explicitly listed single issues regardless of
state, simply run with `--state all`.

## Input File Rules

- Comments `#` and blank lines are ignored.
- Ranges like `1-10` are allowed (ascending only).
- Mixed separators OK: `1-10, 20-25 30`.

## What Gets Transferred

- **Issues** (not PRs) from `--src` that match `--state`.
- The script checks **only the source repo** via GraphQL:
  - If it’s a PR → **excluded: Pull Request**
  - If it’s an issue but `state != --state` → **excluded: wrong state**
  - If not found (e.g., already moved) → **excluded: already transferred / not
    found** (`--trace-redirect` can show the destination URL)

# Examples

## Migrate a Range (Closed Issues 1–50)

```bash
# Issues_To_Transfer.Txt
1-50
```

Dry-run with reasons & redirects:

```bash
python .github/gh_migration/bulk_transfer_issues.py \
  --src causify-ai/cmamp \
  --dst causify-ai/csfy \
  --file .github/gh_migration/issues_to_transfer.txt \
  --state closed \
  --dry-run --why --trace-redirect --max-title 100
```

Execute:

```bash
python .github/gh_migration/bulk_transfer_issues.py \
  --src causify-ai/cmamp \
  --dst causify-ai/csfy \
  --file .github/gh_migration/issues_to_transfer.txt \
  --state closed \
  --sleep 2
```

## Migrate Specific Single Issues Regardless of State

```bash
# Issues_To_Transfer.Txt
13107
42 77 123
```

Run with `--state all`:

```bash
python .github/gh_migration/bulk_transfer_issues.py \
  --src causify-ai/cmamp \
  --dst causify-ai/csfy \
  --file .github/gh_migration/issues_to_transfer.txt \
  --state all \
  --dry-run --why
```

## Generate a Closed-Issues List Up to #400 (Optional Helper)

If you have the GitHub CLI installed, you can quickly build a list:

```bash
gh issue list -R causify-ai/cmamp --state closed --limit 10000 --json number \
  --jq '.[].number' | awk '$1>=1 && $1<=400' \
  > .github/gh_migration/issues_to_transfer.txt
```

## What Transfers & What Doesn’T (Github Behavior)

- ✅ **Transfers**: Issue body, comments, author, assignees
- ⚠️ **Labels & milestones**: Preserved **only if identical** ones exist in the
  destination; otherwise they drop
- ❌ **Pull Requests**: Cannot be transferred as issues

**Tip (optional pre-step):** if you need parity, create matching
labels/milestones in the destination repo first.

# Troubleshooting

**"No issues matched the requested ranges and state ..."** – Your `--state` may
be too strict; try `--state all`

**"Excluded: is a Pull Request"** – GitHub shares the number space between
issues and PRs; PRs are skipped

**"Not found in source (likely transferred)"** – Use `--trace-redirect` to
reveal the destination URL

**Auth / permissions** – Ensure your token has repo access to both repos (and
SSO is authorized if applicable)

**Rate limits** – Increase `--sleep` (e.g., `--sleep 3`) for very large batches

# Idempotency & Safety

- Safe to re-run: already-transferred numbers will be reported as "not found in
  source (likely transferred)" and won’t cause duplicates
- Always **dry-run first** on large ranges

## Exit Codes

* `0` – Success (Transfers Completed or Dry-Run Finished)
* `1` – Invalid Input / No Eligible Issues After Validation / Token or Repo
  error

# Maintenance Notes (For Developers)

## High-Level Algorithm

1. Parse `issues_to_transfer.txt` → expand ranges → de-duplicate & sort
2. For each number: GraphQL `issueOrPullRequest(number:)` in **source**
   - `Issue` → check state; collect title & URL if eligible
   - `PullRequest` → exclude with reason
   - `None` → treat as not found; optionally `--trace-redirect` to show
     destination URL

3. Print plan + exclusions
4. If not `--dry-run`, `transferIssue` each eligible number (sleep between
   calls)

## Known Limitations

- PRs cannot be transferred
- If labels/milestones don’t exist in destination, they are dropped
- Destination issue numbers won’t match source numbers (GitHub re-numbers)

# Appendix: Common Command Snippets

**Quickly verify a single number by URL redirection (manual check):**

```bash
python - <<'PY'
import requests
n=1
u=f"https://github.com/causify-ai/cmamp/issues/{n}"
r=requests.get(u, allow_redirects=True, timeout=20)
print(f"#{n} -> {r.url}")
PY
```

**Preview titles of a few issues via the script’s dry-run:**

```bash
printf "6 7 9 10\n" > .github/gh_migration/issues_to_transfer.txt
python .github/gh_migration/bulk_transfer_issues.py \
  --src causify-ai/cmamp --dst causify-ai/csfy \
  --file .github/gh_migration/issues_to_transfer.txt \
  --state closed --dry-run --why --max-title 100
```
