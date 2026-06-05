<!-- toc -->

- [`invite_gh_contributors.py` Explanation](#invite_gh_contributorspy-explanation)
  * [Public interface](#public-interface)
  * [Execution flow](#execution-flow)
  * [Key implementation choices](#key-implementation-choices)

<!-- tocstop -->

# `invite_gh_contributors.py` Explanation

This document is about how this script works and flows.

## Public interface

```bash
# Google Sheet Source
dev_scripts_helpers/github/invite_gh_contributors.py \
    --drive_url <google‑sheet‑url>  \
    --gh_token  <github‑pat>       \
    --org_name  <github‑org>       \
    --repo_name <repo>             \
    [--log_level 20]

# CSV source (mutually exclusive with --drive_url)
dev_scripts_helpers/github/invite_gh_contributors.py \
    --csv_file  </path/to/users.csv> \
    --gh_token  <github‑pat>         \
    --org_name  <github‑org>         \
    --repo_name <repo>               \
    [--log_level 20]
```

- **`drive_url`/`csv_file`**: Spreadsheet containing a `GitHub user` column.
- **`gh_token`**: PAT with `repo` scope (or fine‑grained "Repository
  administration").
- **`org_name` / `repo_name`**: identify thtarget repository.
- **`log_level`**: standard Python numeric levels (10 = DEBUG, 20 = INFO).

## Execution flow

```mermaid
flowchart TD
    A[parse CLI args] --> B[init logging]
    B --> C[extract_usernames_from_gsheet/csv]
    C -->|"list[str]"| D[send_invitations]
    D --> E{already collaborator?}
    E -- yes --> F[skip + log]
    E -- no --> G[_invite wrapper]
    G -->|add_to_collaborators| H[GitHub API]
    subgraph Rate-limit
        direction TB
        G
        note("@ratelimit.limits 50 calls / 24h → sleep_and_retry if exceeded")
    end
```

## Key implementation choices

- **Dependency auto‑install**: the small `pip install` loop avoids a separate
  requirements file when the script runs in fresh environments, at the cost of
  start‑up time.
- **Service‑account auth**: credentials path is hard‑coded but can be fed via
  env‑var if desired; the helper supports both.
- **Idempotence**: `repo.has_in_collaborators()` prevents duplicate invites
  counting toward the daily quota.
- **Sleep strategy**: we rely entirely on `ratelimit.sleep_and_retry`, so the
  process may block for hours. Even if the process is terminated, the
  idempotence measure will prevent the added names from contributing to the
  quota
