<!-- toc -->

- [Gitleaks Integration in GitHub Actions](#gitleaks-integration-in-github-actions)
  * [Feature](#feature)
  * [Setup](#setup)
  * [Notification](#notification)
  * [Additional Resource](#additional-resource)

<!-- tocstop -->

# Gitleaks Integration in GitHub Actions

- For more information on Gitleaks, refer to the following documentation:
  - [/docs/tools/git/all.gitleaks.reference.md](/docs/tools/git/all.gitleaks.reference.md)
  - [/docs/tools/git/all.gitleaks.how_to_guide.md](/docs/tools/git/all.gitleaks.how_to_guide.md)

## Feature

- **Automatic Scanning**: Gitleaks runs automatically on every pull request to
  the master branch and for every push to the master branch. This ensures that
  new code is checked before merging
- **Scheduled Scans**: Gitleaks scans are scheduled to run once a day, ensuring
  regular codebase checks even without new commits
- **Workflow Dispatch**: Allows for manual triggering of the Gitleaks scan,
  providing flexibility for ad-hoc code analysis

## Setup

- **GitHub Action Workflow**: The Gitleaks integration is set up as a part of
  the GitHub Actions workflow in the `.github/workflows/gitleaks.yml` file in
  each repo
- **Gitleaks rules**: The rules for Gitleaks used by the workflow are specified
  in `.github/gitleaks-rules.toml`
- **Running Environment**: The workflow runs on `ubuntu-latest` and uses GitHub
  action `gitleaks/gitleaks-action@v2` available on the marketplace

## Notification

- **Slack**: Sends a message to the `build-notifications` Slack channel when the
  workflow fails (e.g., when leaks are detected)

## Additional Resource

- The official GitHub page for Gitleaks -
  [https://github.com/gitleaks/gitleaks](https://github.com/gitleaks/gitleaks)
- For more information about how Gitleaks functions in GH Actions -
  [https://github.com/gitleaks/gitleaks-action/tree/master](https://github.com/gitleaks/gitleaks-action/tree/master)
- The custom ruleset was based on -
  [https://github.com/mazen160/secrets-patterns-db](https://github.com/mazen160/secrets-patterns-db)
