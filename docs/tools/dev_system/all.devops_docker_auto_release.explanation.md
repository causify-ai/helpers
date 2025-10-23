<!-- toc -->

- [Automated Docker Release System Architecture](#automated-docker-release-system-architecture)
  * [Summary](#summary)
  * [Architecture Overview](#architecture-overview)
    + [Core Components](#core-components)
    + [System Diagram](#system-diagram)
  * [Phase 1: Automated Build and Test (Implemented)](#phase-1-automated-build-and-test-implemented)
    + [Components](#components)
  * [Phase 2: Manual Review](#phase-2-manual-review)
  * [Phase 3: Automated Release (Planned)](#phase-3-automated-release-planned)
    + [Team-Based Assignment](#team-based-assignment)
    + [PR Labeling](#pr-labeling)
    + [Invoke Target `docker_release_dev_image_from_ghcr()`](#invoke-target-docker_release_dev_image_from_ghcr)
    + [Release Workflow (`.github/workflows/release_dev_image.yml`)](#release-workflow-githubworkflowsrelease_dev_imageyml)
  * [Resources](#resources)

<!-- tocstop -->

# Automated Docker Release System Architecture

## Summary

- This document explains the architecture and design decisions for the automated
  Docker dev image release system
- The system automatically builds, tests, and releases Docker images on a
  periodic schedule
- It consists of three phases:
  - **Phase 1**: Automated build and test
  - **Phase 2**: Manual review - Team member reviews and merges the PR
  - **Phase 3**: Automated release to registries
- The system uses GitHub Actions, invoke tasks, and GitHub CLI helpers to
  orchestrate the entire workflow

## Architecture Overview

### Core Components

- **Invoke Task** (`docker_build_test_dev_image`): Core automation logic
  - Bumps version (minor by default)
  - Creates GitHub issue and branch
  - Builds local Docker image
  - Runs test suites (currently commented out)
  - Updates changelog
  - Commits and pushes changes
  - Creates PR (ready for review, with reviewer)
  - Tags and pushes `dev-{version}` to GHCR

- **GitHub Actions Workflow**
  (`.github/workflows/dev_image_build_and_test.yml`): Orchestrates the entire
  automated build and test process
  - Triggered weekly by cron schedule or manually
  - Calls `invoke docker_build_test_dev_image --assignee=<username>`

- **GitHub CLI Helpers**: New team management functions
  - `gh_get_org_team_names()`: Fetch organization teams
  - `gh_get_team_member_names()`: Fetch team members
  - Enhanced `gh_create_pr()`: Support for reviewer parameter

- **Version Management** (`bump_version()` in
  [`/helpers/hversion.py)`](/helpers/hversion.py)): New semantic versioning
  function
  - Bumps version numbers (major/minor/patch)
  - Default: minor bump (e.g., 2.2.0 → 2.3.0)

### System Diagram

```mermaid
graph TB
    subgraph "Trigger"
        A[Cron Schedule]
        B[Manual Dispatch]
    end

    subgraph "GitHub Actions"
        D[Workflow Runner]
        D --> E[Setup Environment]
        E --> F[Checkout Code]
        F --> G[Docker Login]
        G --> H[Run Invoke Task]
    end

    subgraph "Phase 1: Build, Test & PR Creation"
        H --> I[Bump Version]
        I --> J[Create Issue]
        J --> K[Create Branch]
        K --> L[Build Image]
        L --> M[Run Tests]
        M --> N[Update Changelog]
        N --> O[Commit Changes]
        O --> P[Push Branch]
        P --> Q[Create PR & Request Review]
        Q --> R[Push to GHCR]
    end

    subgraph "Phase 2: Manual Review"
        R --> S[Team Review]
        S --> T[Merge PR]
    end

    subgraph "Phase 3: Automated Release"
        T --> U[Detect Merge + Label]
        U --> V[Pull Image from GHCR]
        V --> W[Re-tag for ECR & GHCR]
        W --> X[Push to Registries]
    end

    A --> D
    B --> D
```

## Phase 1: Automated Build and Test (Implemented)

Triggered weekly by schedule, the workflow bumps the version, creates a GitHub
issue and branch, builds a Docker image, runs tests (currently commented out),
updates the changelog, commits and pushes changes, creates a PR with reviewer
assigned, and pushes the versioned image (`dev-{version}`) to GHCR for
verification before production release.

### Components

1. **GitHub Actions Workflow**
   (`.github/workflows/dev_image_build_and_test.yml`) - Weekly scheduled
   workflow (Monday at 6 AM UTC) with manual trigger and assignee support
2. **Invoke Target** (`docker_build_test_dev_image()` in
   [`/helpers/lib_tasks_docker_release.py)`](/helpers/lib_tasks_docker_release.py)) -
   Orchestrates the complete build, test, and release pipeline
3. **GitHub CLI Helpers** (`helpers/lib_tasks_gh.py`) - New team management
   functions (`gh_get_org_team_names()`, `gh_get_team_member_names()`) and
   enhanced `gh_create_pr()` with reviewer support
4. **Version Management** (`bump_version()` in
   [`/helpers/hversion.py)`](/helpers/hversion.py)) - Semantic version bumping
   (minor by default: 2.2.0 → 2.3.0)

## Phase 2: Manual Review

This is the critical human gate between automated build and automated release.
After Phase 1 completes, the assigned team member reviews the PR, validates the
changes (changelog, version, poetry.lock), optionally tests the image from GHCR,
and merges to master. The PR is automatically created as "Ready for review" with
a reviewer assigned. Quality gates: all status checks pass, properly formatted
changelog, no merge conflicts, valid sequential version number.

## Phase 3: Automated Release

When the PR from Phase 1 is merged, an automated workflow 
(`.github/workflows/dev_image_release.yml`) detects the merge event with the 
"Automated release" label, pulls the verified image from GHCR, re-tags it for 
production registries (AWS ECR, etc.), and pushes to all target registries.

### Team-Based Assignment

**Configuration:**

- Add to `repo_config.yaml`:
  ```yaml
  release_team: "dev_system" # GitHub team slug
  ```

**Implementation plan:**

- Fetch team members using `gh_get_team_member_names()`
- Assign issue to all team members (multi-assignee)
- Request PR review from team (not individual)
- Format: `--reviewer team:org/team-slug`

**Benefits:**

- Distributes responsibility across team
- Any team member can review and merge
- Reduces single point of failure

### PR Labeling

**Label name:** `Automated release`

**Purpose:**

- Identifies PRs created by automated workflow
- Used as trigger for release workflow
- Enables filtering and automation

**Implementation:**

```python
# In gh_create_pr():
if is_automated_release:
    cmd += ' --label "Automated release"'
```

### Invoke Target `docker_tag_push_dev_image_from_ghcr()`

Gets the version from changelog, pulls the versioned dev image from GHCR,
re-tags it for target registries (GHCR and AWS ECR), pushes to all configured 
registries, and verifies the images. Supports dry-run mode for testing.

### Release Workflow (`.github/workflows/dev_image_release.yml`)

**Trigger:**

- Event: `pull_request`
- Types: `[closed]`
- Condition: `if: github.event.pull_request.merged == true`
- Label filter: Check for `Automated release` label
- Also supports manual `workflow_dispatch`

**Steps:**

- Execute `invoke docker_tag_push_dev_image_from_ghcr --dry-run`
