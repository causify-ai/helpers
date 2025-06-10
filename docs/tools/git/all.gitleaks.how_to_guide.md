<!-- toc -->

- [Gitleaks How to Guide](#gitleaks-how-to-guide)
  * [How to deal with false positives](#how-to-deal-with-false-positives)
  * [How to clean leaks from previous commits in PR](#how-to-clean-leaks-from-previous-commits-in-pr)
  * [How to run Gitleaks locally](#how-to-run-gitleaks-locally)

<!-- tocstop -->

# Gitleaks How to Guide

## How to deal with false positives

1. Use inline comments to allow specific lines of code

```bash
> aws_access_key_id=*** # gitleaks:allow
```

2. Add the fingerprint to the `.gitleaksignore` file

3. Adjust the rules in the `gitleaks-rules.toml` file

## How to clean leaks from previous commits in PR

- Sometimes leaks are committed to a PR, even after we remove them, the leaks
  still exist in the commit history
- Because of the leaks in the commit history, the Gitleaks GH Actions will fail
- To remove the leaks from the commit history, we can use the following methods:

- Option 1: Rebase and squash the all commits in the PR into a single commit
  - Use this if it is okay to discard all the commit history in the PR

  ```bash
  # Checkout the PR branch
  > git checkout <PR-branch-name>

  # Reset to the base commit but keep changes staged
  > git reset --soft $(git merge-base HEAD master)

  # Create a new commit with all changes
  > git commit -m "<commit-message>"

  # Force push to the remote branch
  > git push -f
  ```

- Option 2: Rebase and squash only the commits that contain the leaks
  - Use this if we want to keep some commit history in the PRs
  - See [this guide](https://www.datacamp.com/tutorial/git-squash-commits) for
    more details on how to rebase and squash commits

## How to run Gitleaks locally

The easiest way to run gitleaks locally is with docker.

- First we pull the image:

  ```bash
  > docker pull zricethezav/gitleaks:latest
  ```

- Then we run it from the root of the repo:
  - Scan git repositories for secrets (including git history)

  ```bash
  > docker run -v $(pwd):/path zricethezav/gitleaks:latest git /path -v -c /path/.github/gitleaks-rules.toml
      ○
      │╲
      │ ○
      ○ ░
      ░    gitleaks

  7:52PM INF 1540 commits scanned.
  7:52PM INF scanned ~51542901 bytes (51.54 MB) in 46.4s
  7:52PM INF no leaks found
  ```
  - Scan directories or files for secrets

  ```bash
  > docker run -v $(pwd):/path zricethezav/gitleaks:latest dir /path -v -c /path/.github/gitleaks-rules.toml
      ○
      │╲
      │ ○
      ○ ░
      ░    gitleaks

  8:00PM INF scanned ~23901530 bytes (23.90 MB) in 26.1s
  8:00PM INF no leaks found
  ```
