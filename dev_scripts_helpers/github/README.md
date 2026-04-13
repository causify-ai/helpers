<!-- toc -->

- [Summary](#summary)
- [Structure of the Dir](#structure-of-the-dir)
- [Description of Files](#description-of-files)
- [Description of Executables](#description-of-executables)
  * [`to_github.py`](#to_githubpy)
    + [What It Does](#what-it-does)
    + [Examples](#examples)
  * [`set_secrets_and_variables.py`](#set_secrets_and_variablespy)
    + [What It Does](#what-it-does-1)
    + [Examples](#examples-1)
  * [`sync_gh_issue_labels.py`](#sync_gh_issue_labelspy)
    + [What It Does](#what-it-does-2)
    + [Examples](#examples-2)
  * [`sync_gh_projects.py`](#sync_gh_projectspy)
    + [What It Does](#what-it-does-3)
    + [Examples](#examples-3)
  * [Dockerized Variants](#dockerized-variants)
    + [What They Do](#what-they-do)

<!-- tocstop -->

# Summary

This directory contains tools for managing GitHub repositories, including:
- Converting local file paths to GitHub URLs
- Synchronizing issue labels
- Managing project fields
- Handling repository settings and collaborator invitations.
The tools support both direct execution and Dockerized execution for dependency
isolation.

# Structure of the Dir

- `gh_migration/`
  - Tools and guides for migrating GitHub issues between repositories
- `labels/`
  - Label manifest files and backup storage for GitHub issue labels
- `labels/backup/`
  - Backup copies of label configurations from various repositories
- `settings/`
  - YAML configuration files for GitHub repository settings and branch protection
- `test/`
  - Unit tests and test outcomes for GitHub synchronization tools

# Description of Files

- `__init__.py`
  - Empty module initialization file for the github package
- `dockerized_invite_gh_contributors.py`
  - Dockerized script to invite GitHub collaborators from Google Sheets or CSV files
- `dockerized_sync_gh_issue_labels.py`
  - Dockerized script to synchronize GitHub issue labels using pygithub dependency
- `dockerized_sync_gh_repo_settings.py`
  - Dockerized script to synchronize GitHub repository settings and branch protection rules
- `invite_gh_contributors.py`
  - Wrapper script to invite GitHub collaborators by running dockerized version in container
- `invite_github_collaborator.py`
  - Direct API script to check and invite individual GitHub collaborators to repositories
- `set_secrets_and_variables.py`
  - Batch upload GitHub secrets and variables from JSON file using gh CLI
- `sync_gh_issue_labels.py`
  - Wrapper script to synchronize GitHub issue labels by running dockerized version
- `sync_gh_projects.py`
  - Script to sync GitHub Project fields and views from template project to destination
- `to_github.py`
  - Convert local file paths to GitHub URLs with branch awareness and browser integration

# Description of Executables

## `to_github.py`

### What It Does

- Converts local file or directory paths to corresponding GitHub URLs.
- Generates URLs using the repository's remote origin and current or master branch.
- Supports opening URLs in browser and copying to clipboard.
- Issues warning if the specified file or directory does not exist.

### Examples

- Convert file path to GitHub URL:
  ```bash
  > ./to_github.py --input helpers/hdbg.py
  ```

- Use master branch instead of current branch:
  ```bash
  > ./to_github.py --input helpers/hdbg.py --use_master
  ```

- Open URL in browser:
  ```bash
  > ./to_github.py --input data605/tutorials/ --open
  ```

- Copy URL to clipboard:
  ```bash
  > ./to_github.py --input helpers/hdbg.py --copy
  ```

## `set_secrets_and_variables.py`

### What It Does

- Batch uploads GitHub secrets and variables from a JSON file to a repository.
- Uses the gh CLI tool to set or remove repository secrets and variables.
- Validates that values are non-empty before uploading.
- Supports dry run mode to preview changes without applying them.

### Examples

- Upload secrets and variables from JSON file:
  ```bash
  > ./set_secrets_and_variables.py \
      --file 'dev_scripts/github/vars.json' \
      --repo 'cryptomtc/cmamp_test'
  ```

- Preview changes without applying:
  ```bash
  > ./set_secrets_and_variables.py \
      --file 'vars.json' \
      --repo 'owner/repo' \
      --dry_run
  ```

- Remove secrets and variables:
  ```bash
  > ./set_secrets_and_variables.py \
      --file 'vars.json' \
      --repo 'owner/repo' \
      --remove
  ```

## `sync_gh_issue_labels.py`

### What It Does

- Synchronizes GitHub issue labels from a YAML manifest file to a repository.
- Builds Docker container dynamically if necessary for dependency isolation.
- Supports dry run mode to preview label changes without applying them.
- Can backup existing labels before synchronization.

### Examples

- Synchronize labels with dry run and backup:
  ```bash
  > ./sync_gh_issue_labels.py \
      --input_file ./dev_scripts_helpers/github/labels/gh_issues_labels.yml \
      --owner causify-ai \
      --repo tutorials \
      --token_env_var GITHUB_TOKEN \
      --dry_run \
      --backup
  ```

- Apply label synchronization:
  ```bash
  > ./sync_gh_issue_labels.py \
      --input_file ./labels/gh_issues_labels.yml \
      --owner myorg \
      --repo myrepo \
      --token_env_var GITHUB_TOKEN
  ```

## `sync_gh_projects.py`

### What It Does

- Synchronizes GitHub Project fields and views from a template project to destination project.
- Adds missing global fields from source template to destination project.
- Logs warnings for views missing in destination without creating them.
- Supports dry run mode to preview changes without applying them.

### Examples

- Sync project fields from template:
  ```bash
  > ./sync_gh_projects.py \
      --owner "causify-ai" \
      --src-template "[TEMPLATE] Causify Project" \
      --dst-project "Buildmeister"
  ```

- Preview changes with dry run:
  ```bash
  > ./sync_gh_projects.py \
      --owner "causify-ai" \
      --src-template "[TEMPLATE] Causify Project" \
      --dst-project "Buildmeister" \
      --dry-run
  ```

- Enable debug logging:
  ```bash
  > ./sync_gh_projects.py \
      --owner "causify-ai" \
      --src-template "[TEMPLATE] Causify Project" \
      --dst-project "Buildmeister" \
      -v DEBUG
  ```

## Dockerized Variants

### What They Do

- `dockerized_sync_gh_issue_labels.py` and `dockerized_sync_gh_repo_settings.py`
  are internal tools called automatically by their wrapper scripts.
- These execute synchronization operations within Docker containers to ensure
  dependencies like pygithub are available.
- `dockerized_invite_gh_contributors.py` handles GitHub collaborator invitations
  within Docker, respecting the 50-invite per 24-hour GitHub rate limit.
- Users typically do not call these directly - use the wrapper scripts instead.
