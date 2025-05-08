<!-- toc -->

- [GitHub Project Sync Tool](#github-project-sync-tool)
  * [Purpose](#purpose)
    + [What It Actually Syncs](#what-it-actually-syncs)
    + [Features:](#features)
  * [How It Works](#how-it-works)
    + [Step-by-Step:](#step-by-step)
  * [Limitations](#limitations)
  * [Current State & Technical Insights](#current-state--technical-insights)
  * [Recommended Usage](#recommended-usage)
    + [1. To preview what changes would be made:](#1-to-preview-what-changes-would-be-made)
    + [2. To apply changes:](#2-to-apply-changes)
  * [Example Scenario](#example-scenario)
    + [Source Project `[TEMPLATE] Causify Project`](#source-project-template-causify-project)
    + [Destination Project `Buildmeister`](#destination-project-buildmeister)
    + [What the Script Will Do:](#what-the-script-will-do)
  * [Final Notes](#final-notes)
    + [When GitHub adds support for:](#when-github-adds-support-for)

<!-- tocstop -->

# GitHub Project Sync Tool

This guide explains how the
[`sync_gh_projects.py`](/dev_scripts_helpers/github/sync_gh_projects.py) tool
works, what it's designed to do, and the known limitations due to GitHub's
Projects (Beta) API constraints. This tool has many limitations currently due to
restricted GraphQL API support for ProjectV2, especially around views, layout,
and ordering.

## Purpose

This tool synchronizes the `structure` of a GitHub Project from a source
template project to a target destination project. It helps teams quickly align
project configuration without manually replicating fields.

### What It Actually Syncs

- `Fields`: These are the global columns in your project (e.g., Status,
  Assignees, Labels). When created via the API, they are automatically visible
  in all views. There is no API support to add fields specifically to one view
  or to hide them from others
- `Views`: These are saved layouts (e.g., "Backlog", "Current sprint"). However,
  the API currently does not support creating views, so this script only
  compares view names and logs a warning if any are missing in the destination

### Features:

- Adds `missing global fields` from the template into the destination project
- Logs a warning about any `missing views` in the destination project
- Supports a `dry-run mode` (`--dry-run`) to preview intended changes without
  modifying anything
- Supports a `verbose mode` (`--verbose`) to display detailed command logs

## How It Works

### Step-by-Step:

1. Lists all Projects V2 for the specified GitHub `--owner` using
   `gh project list`
2. Locates the source (`--src-template`) and destination (`--dst-project`) by
   title
3. Queries each project's structure using GraphQL to fetch:
   - Global `fields`
   - Global `views` (names only)

4. Compares structures:
   - If a field is in the source but not in the destination, it is added using
     `addProjectV2Field`.
   - If a view is in the source but not in the destination, it is **not
     created** but logged with a warning.

## Limitations

| Capability                          | Supported | Notes                                              |
| ----------------------------------- | --------- | -------------------------------------------------- |
| Create missing global fields        | Yes       | Done via GraphQL `addProjectV2Field` mutation      |
| Detect and warn about missing views | Yes       | Logs missing view names, but cannot recreate them  |
| Delete extra fields/views           | No        | Not implemented (non-destructive by design)        |
| Reorder fields or views             | No        | API does not expose position or ordering mutations |
| View-specific field visibility      | No        | GraphQL only exposes global field presence         |
| View filters, sort orders, layout   | No        | Not accessible via GitHub's GraphQL API            |

## Current State & Technical Insights

- `All fields in GitHub Projects are global` - They are shared across views.
  While you can hide fields per view in the UI, this cannot be accessed or
  modified via the API.
- `There is no GraphQL mutation to create or configure views`
  (`addProjectV2View` does not exist) - Hence, the tool only checks for view
  names and alerts when missing.
- `The script avoids destructive behavior` - It does not delete fields or views
  that appear extra in the destination project.
- `Newly added fields will be visible across all views` unless manually hidden
  in the UI.
- `You must still manually create views or configure filters, grouping, and sorting`,
  as none of that is available through GitHub's API.

## Recommended Usage

### 1. To preview what changes would be made:

```bash
python sync_gh_projects.py \
  --owner causify-ai \
  --src-template "[TEMPLATE] Causify Project" \
  --dst-project "Buildmeister" \
  --dry-run --verbose
```

This will output:

- Fields in both source and destination
- Views in both source and destination
- Fields that would be created
- Views that are missing but cannot be added via script

### 2. To apply changes:

```bash
python sync_gh_projects.py \
  --owner causify-ai \
  --src-template "[TEMPLATE] Causify Project" \
  --dst-project "Buildmeister"
```

This will:

- Add any missing fields that are present in the source template and absent in
  the destination.
- Warn about any views missing in the destination.
- Not reorder, delete, or modify any existing structure.

---

## Example Scenario

### Source Project `[TEMPLATE] Causify Project`

`Fields`:

- Title, Assignees, Status, Labels, Milestone, Repository, Estimate

`Views`:

- Backlog, Current sprint, All issues

### Destination Project `Buildmeister`

`Fields`:

- Title, Assignees, Status, Labels, Milestone

`Views`:

- Backlog, Current sprint

### What the Script Will Do:

- It will `add` the missing fields: `Repository`, `Estimate`
- It will `log a warning` that the view `All issues` is missing
- It will `not` remove or alter any other structure

## Final Notes

This tool is ideal for aligning the structure of GitHub Projects across teams or
environments where a base template is used. It helps reduce manual setup effort
and avoids configuration drift.

Because GitHub's ProjectV2 API is still limited, this tool takes a conservative
approach:

- It only creates fields
- It does not delete or modify
- It only checks for view presence by name

### When GitHub adds support for:

- View creation
- View filters and layout configuration
- Field ordering

...this tool can be extended to do more complete synchronization.
