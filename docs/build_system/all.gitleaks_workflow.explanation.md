

<!-- toc -->

- [Gitleaks Integration in GitHub Actions](#gitleaks-integration-in-github-actions)
  * [Overview](#overview)
  * [Features](#features)
  * [Setup](#setup)
  * [Rules and Exceptions](#rules-and-exceptions)
    + [1. `title`](#1-title)
    + [2. Allowlist](#2-allowlist)
    + [3. Rules extension](#3-rules-extension)
    + [4. Rules](#4-rules)
    + [.gitleaksignore](#gitleaksignore)
  * [Notifications](#notifications)
  * [Running Gitleaks locally](#running-gitleaks-locally)
  * [Additional Resources](#additional-resources)

<!-- tocstop -->

# Gitleaks Integration in GitHub Actions

- Refer the follow docs for more information on Gitleaks:
  - [/docs/tools/git/all.gitleaks.reference.md](/docs/tools/git/all.gitleaks.reference.md)
  - [/docs/tools/git/all.gitleaks.reference.md](/docs/tools/git/all.gitleaks.reference.md)

### Features

- **Automatic Scanning**: Gitleaks runs automatically on every pull request to
  the master branch and for every push to the master branch. This ensures that
  new code is checked before merging
- **Scheduled Scans**: Gitleaks scans are scheduled to run once a day, ensuring
  regular codebase checks even without new commits
- **Workflow Dispatch**: Allows for manual triggering of the Gitleaks scan,
  providing flexibility for ad-hoc code analysis

### Setup

- **GitHub Action Workflow**: The Gitleaks integration is set up as a part of
  the GitHub Actions workflow in the [`.github/workflows/gitleaks.yml` file in
  each repo
- **Running Environment**: The workflow runs on `ubuntu-latest` and uses GitHub
  action `gitleaks/gitleaks-action@v2` available on the marketplace.

### Notifications

- **Slack**: Send a message to the `build-notifications` Slack channel if the
  workflow fails (e.g. if the leaks are detected)

### Additional Resources

- The official GitHub page for Gitleaks - https://github.com/gitleaks/gitleaks
- For more information about how Gitleaks functions in GH Actions -
  https://github.com/gitleaks/gitleaks-action/tree/master
- The custom ruleset was based on -
  https://github.com/mazen160/secrets-patterns-db
