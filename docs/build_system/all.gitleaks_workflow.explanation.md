

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

## Overview

This document provides an overview and guidance on the integration of Gitleaks,
a SAST tool, into the GitHub Actions workflow. Gitleaks is used for detecting
and preventing hardcoded secrets like passwords, api keys, and tokens in git
repos.

## Features

- **Automatic Scanning**: Gitleaks runs automatically on every pull request to
  the master branch and for every push to the master branch. This ensures that
  new code is checked before merging.
- **Scheduled Scans**: Additionally, Gitleaks scans are scheduled to run once a
  day, ensuring regular codebase checks even without new commits.
- **Workflow Dispatch**: The integration allows for manual triggering of the
  Gitleaks scan, providing flexibility for ad-hoc code analysis.

## Setup

- **GitHub Action Workflow**: The Gitleaks integration is set up as a part of
  the GitHub Actions workflow in the
  [`gitleaks.yml`](https://github.com/cryptokaizen/cmamp/blob/master/.github/workflows/gitleaks.yml)
  file.
- **Running Environment**: The workflow runs on `ubuntu-latest` and uses GitHub
  action `gitleaks/gitleaks-action@v2` available on the marketplace.

## Rules and Exceptions

The rules for Gitleaks are specified in the
[`gitleaks-rules.toml`](https://github.com/cryptokaizen/cmamp/blob/master/.github/gitleaks-rules.toml)
file located in the `.github/` directory. The file consists of:

### 1. `title`

A name for the configuration file.

### 2. Allowlist

Used for exceptions on a file level, i.e. to exclude whole files. For a line
level exceptions see `.gitleaksignore` section

- `[allowlist]` - Flag that starts the allowlist.
- `description` - A short description for the allowlist.
- `paths` - Path to the file to be ignored. It has to include the ruleset for
  the Gitleaks, otherwise it would detect itself as leaks.

The whole allowlist then looks like this:

```toml
[allowlist]
description = "global allow lists"
paths = [
    '''.github/gitleaks-rules.toml''',
]
```

### 3. Rules extension

We can extend our custom ruleset to also include the default ruleset provided by
Gitleaks.

- `[extend]` - The flag that extends the custom ruleset. Has to be used with
  `useDefault = true`:

```toml
[extend]
useDefault = true
```

### 4. Rules

The file is then followed by a set of rules. Each rule is defined with:

- `id` - A unique identifier for each rule
- `description` - Short human readable description of the rule
- `regex` - Golang regular expression used to detect secrets
- `tags` - Array of strings used for metadata and reporting purposes

The rule as a whole then looks like this:

```toml
[[rules]]
    id = "rule2"
    description = '''AWS API Key'''
    regex = '''AKIA[0-9A-Z]{16}'''
    tags = ["secret"]
```

### .gitleaksignore

To prevent specific lines of code from being scanned by Gitleaks, we can use the
`.gitleaksignore` file. It uses "fingerprints" to define the leaks. Gitleaks
itself generates these fingerprints when it detects a leak. Then it can be
simply added to the file. The file can be placed at the root directory of a
repo. Examples of a fingerprint:
```
> ck.infra/infra/terraform/environments/preprod/ap-northeast-1/terraform.tfvars:rule3:429
> 93f292c3dfa2649ef91f8925b623e79546fa992e:README.md:aws-access-token:121
```

## Notifications

To be implemented.

## Running Gitleaks locally

The easiest way to run gitleaks locally is with docker. First we pull the image:

```docker
docker pull zricethezav/gitleaks:latest
```

Then we run it from the root of the repo:

```docker
docker run \
  -v "$(pwd):/mnt/source" \ # mounts a volume into the Docker container
  -v "$(pwd)/.github/gitleaks-rules.toml:/mnt/gitleaks-rules.toml" \ # mounts the configuration file
  zricethezav/gitleaks:latest detect \ # docker image + `detect` command used for scanning
  --source="/mnt/source" \ # the source directory that Gitleaks should scan
  --config="/mnt/gitleaks-rules.toml" \ # use the custom configuration file
  --no-git \ # perform a filesystem-based scan instead of a Git history scan
  --report-format="json" \ # the format of the report
  --report-path="/mnt/source/gitleaks-report.json" # output path for the report
```

## Additional Resources

- The official GitHub page for Gitleaks - https://github.com/gitleaks/gitleaks
- For more information about how Gitleaks functions in GH Actions -
  https://github.com/gitleaks/gitleaks-action/tree/master
- The custom ruleset was based on -
  https://github.com/mazen160/secrets-patterns-db
