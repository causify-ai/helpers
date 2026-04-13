# Synchronize GitHub repository settings

<!-- toc -->

- [Overview](#overview)
- [Prerequisites](#prerequisites)
  * [GitHub token](#github-token)
- [Settings manifest file structure](#settings-manifest-file-structure)
- [How to synchronize repository settings](#how-to-synchronize-repository-settings)
- [Troubleshooting](#troubleshooting)

<!-- tocstop -->

- TODO(sandeep): Update the script path references once the dockerized
  executable is implemented

## Overview

- The
  [`dockerized_sync_gh_repo_settings.py`](/dev_scripts_helpers/github/dockerized_sync_gh_repo_settings.py)
  script helps to export and synchronize GitHub repository settings and branch
  protection rules through a settings manifest file

- The script supports two operations:
  - `export`: write current repository settings to a YAML file
  - `sync`: apply the settings defined in a YAML file to a repository

- The script uses `PyGithub` library to interact with the GitHub API

- The script is a dockerized executable (i.e., runs in a Docker container to
  ensure that all the dependencies are verified, e.g., `PyGitHub`)

- Every time you run sync the script saves a backup of the current settings so
  you can roll back if needed
  - The settings are backed up in the current working directory

## Prerequisites

### GitHub token

- You need a GitHub token with appropriate repository management permissions
- Store the token in an environment variable and verify it:
  ```bash
  > echo $GITHUB_TOKEN
  ```

## Settings manifest file structure

- In each repo there are two parts of a configuration we need to set

- The "repository settings" section controls basic repository configuration:

  ```yaml
  repository_settings:
    name: "repo-name"
    description: "Repository description"
    homepage: "https://example.com"
    private: true
    archived: false
    has_issues: true
    has_projects: true
    has_wiki: true
    allow_squash_merge: true
    allow_merge_commit: true
    allow_rebase_merge: true
    delete_branch_on_merge: true
    enable_automated_security_fixes: true
    enable_vulnerability_alerts: true
    topics:
      - topic1
      - topic2
  ```

- The "branch protection" section defines rules for protected branches:

  ```yaml
  branch_protection:
    main:
      enforce_admins: true
      allow_force_pushes: false
      allow_deletions: false
      required_status_checks:
        strict: true
        contexts:
          - "run tests"
      required_pull_request_reviews:
        dismiss_stale_reviews: true
        require_code_owner_reviews: true
        required_approving_review_count: 2
        dismissal_restrictions:
          users:
            - "user1"
          teams:
            - "team1"
      restrictions:
        users:
          - "maintainer1"
          - "maintainer2"
        teams:
          - "developers"
          - "admins"
  ```

- You can use two reference files to help configure your repository:

  1. `Common repository settings`
     - Find the file at
       [/dev_scripts_helpers/github/settings/common_repo_settings.yaml](/dev_scripts_helpers/github/settings/common_repo_settings.yaml)
     - This file contains standard settings that we use across multiple
       repositories
     - Start with this file when you want to maintain consistency with other
       repositories

  2. `Template settings`
     - Find the file at
       [/dev_scripts_helpers/github/settings/template_repo_settings.yaml](/dev_scripts_helpers/github/settings/template_repo_settings.yaml)
     - This template shows all available configuration options with example
       values
     - Use this file when you need to create a new settings file from scratch
     - You can remove any settings parameters you don't need; the script will
       handle missing entries

## How to synchronize repository settings

- View more information about the script's arguments:

  ```bash
  > dockerized_sync_gh_repo_settings.py --help
  ```

  ```bash
  > dockerized_sync_gh_repo_settings.py export --help
  ```

  ```bash
  > dockerized_sync_gh_repo_settings.py sync --help
  ```

- Export repository settings to a YAML file:

  ```bash
  > dockerized_sync_gh_repo_settings.py export \
      --output_file settings.yaml \
      --owner your-org \
      --repo your-repo \
      --token_env_var GITHUB_TOKEN
  ```

- Synchronize settings from a YAML file to a repository:

  ```bash
  > dockerized_sync_gh_repo_settings.py sync \
      --input_file settings.yaml \
      --owner your-org \
      --repo your-repo \
      --token_env_var GITHUB_TOKEN
  ```

- Preview changes without applying them by adding `--dry_run` flag:

  ```bash
  > dockerized_sync_gh_repo_settings.py sync \
      --input_file settings.yaml \
      --owner your-org \
      --repo your-repo \
      --token_env_var GITHUB_TOKEN \
      --dry_run
  ```

## Troubleshooting

1. For permission errors:
   - Verify your GitHub token has sufficient permissions
   - Check your repository admin access

2. If settings are not applied:
   - Run with `--dry_run` to preview changes
   - Verify the manifest file structure
   - Check all required fields are present
