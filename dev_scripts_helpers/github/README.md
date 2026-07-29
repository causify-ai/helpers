# GitHub

GitHub repository management tools. Supports label synchronization, project field
syncing, secret management, URL conversion, and batch collaborator invitations
with Dockerized execution for dependency isolation.

## Structure of the Dir

- `gh_migration/`
  - Tools and guides for GitHub issue migration between repositories
- `labels/`
  - GitHub issue label manifest files and configuration backups
- `settings/`
  - Repository settings and branch protection YAML configurations
- `test/`
  - Unit tests for GitHub synchronization tools

## Description of Files

- `__init__.py`
  - Package initialization file
- `dockerized_invite_gh_contributors.py`
  - Dockerized script to batch invite GitHub collaborators from Google Sheets
- `dockerized_sync_gh_issue_labels.py`
  - Dockerized script to synchronize GitHub issue labels via pygithub
- `dockerized_sync_gh_repo_settings.py`
  - Dockerized script to synchronize repository settings and branch protection
- `invite_gh_contributors.py`
  - Wrapper script to run Dockerized collaborator invitations
- `invite_github_collaborator.py`
  - Direct API for inviting individual GitHub collaborators
- `set_secrets_and_variables.py`
  - Batch upload GitHub secrets and variables from JSON file
- `sync_gh_issue_labels.py`
  - Wrapper script to synchronize GitHub issue labels
- `sync_gh_projects.py`
  - Sync GitHub Project fields and views from template to destination
- `to_github.py`
  - Convert local file paths to GitHub URLs with branch awareness
- `run_local_ci.py`
  - Run local CI regression tests on a schedule or once

# Description of Executables

## `to_github.py`

### What It Does

- Converts local file and directory paths to GitHub repository URLs
- Uses repository remote origin and current or master branch for URL generation
- Supports opening URLs in browser and copying to clipboard
- Warns if specified path does not exist

### Examples

- Convert file path to GitHub URL:
  ```bash
  > ./to_github.py --input helpers/hdbg.py
  ```

- Use master branch for URL:
  ```bash
  > ./to_github.py --input helpers/hdbg.py --use_master
  ```

- Open URL in browser:
  ```bash
  > ./to_github.py --input docs/readme.md --open
  ```

- Copy URL to clipboard:
  ```bash
  > ./to_github.py --input helpers/hdbg.py --copy
  ```

## `set_secrets_and_variables.py`

### What It Does

- Batch uploads GitHub secrets and variables from JSON configuration
- Uses gh CLI for secret management and environment variable configuration
- Validates non-empty values before uploading
- Supports dry run and removal operations

### Examples

- Upload secrets and variables:
  ```bash
  > ./set_secrets_and_variables.py \
      --file vars.json \
      --repo owner/repo
  ```

- Preview changes with dry run:
  ```bash
  > ./set_secrets_and_variables.py \
      --file vars.json \
      --repo owner/repo \
      --dry_run
  ```

- Remove secrets:
  ```bash
  > ./set_secrets_and_variables.py \
      --file vars.json \
      --repo owner/repo \
      --remove
  ```

## `sync_gh_issue_labels.py`

### What It Does

- Synchronizes GitHub issue labels from YAML manifest to repository
- Builds Docker container for dependency isolation if needed
- Creates label backups before synchronization
- Supports dry run mode for preview

### Examples

- Sync labels with backup and dry run:
  ```bash
  > ./sync_gh_issue_labels.py \
      --input_file labels.yml \
      --owner org \
      --repo repo \
      --token_env_var GITHUB_TOKEN \
      --dry_run --backup
  ```

- Apply label synchronization:
  ```bash
  > ./sync_gh_issue_labels.py \
      --input_file labels.yml \
      --owner org \
      --repo repo \
      --token_env_var GITHUB_TOKEN
  ```

## `sync_gh_projects.py`

### What It Does

- Synchronizes GitHub Project fields and views from template to destination
- Adds missing global fields from source template project
- Logs warnings for destination views without creating them
- Supports dry run mode for preview

### Examples

- Sync project fields:
  ```bash
  > ./sync_gh_projects.py \
      --owner "org" \
      --src-template "TemplateProject" \
      --dst-project "TargetProject"
  ```

- Preview with dry run:
  ```bash
  > ./sync_gh_projects.py \
      --owner "org" \
      --src-template "TemplateProject" \
      --dst-project "TargetProject" \
      --dry-run
  ```

- Run with debug logging:
  ```bash
  > ./sync_gh_projects.py \
      --owner "org" \
      --src-template "TemplateProject" \
      --dst-project "TargetProject" \
      -v DEBUG
  ```

## `run_local_ci.py`

### What It Does

- Runs regression tests for current directory and git submodules
- Executes `pytest_multi_build.py` and `pytest_failed_multi_build.py` for CI testing
- Supports single run or daily scheduled execution via daemon mode
- Validates repository is at master branch before running tests
- Cleans working directory with `git clean -fd` before test execution
- Logs all output to timestamped files for debugging

### Examples

- Run tests once immediately:
  ```bash
  > ./run_local_ci.py
  ```

- Run tests at specific time in daemon mode:
  ```bash
  > ./run_local_ci.py --start_time 2am --daemon
  ```

- Run with specific pytest target:
  ```bash
  > ./run_local_ci.py --pytest_target "helpers/test/"
  ```

- Run without master branch check:
  ```bash
  > ./run_local_ci.py --no_master_check
  ```

- Run on specific directories:
  ```bash
  > ./run_local_ci.py --repo_dirs . helpers --daemon --start_time 14:30
  ```

- Run with debug logging:
  ```bash
  > ./run_local_ci.py -v DEBUG --daemon --start_time 2am
  ```
