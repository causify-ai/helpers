<!-- toc -->

- [Inviting GitHub Collaborators from Google Sheets](#inviting-github-collaborators-from-google-sheets)
  * [Prerequisites](#prerequisites)
  * [Running the script](#running-the-script)

<!-- tocstop -->

# Inviting GitHub Collaborators from Google Sheets

## Prerequisites

- **`uv`** installed: the script declares its Python dependencies inline and
  `uv` installs them on the first run

- **GitHub token** with the classic **`repo`** scope, or a fine-grained token
  granting Repository administration for the target repository. The script
  reads it from the `GITHUB_TOKEN` env var. If the env var is not set, it uses
  the token of the logged-in `gh` CLI (`gh auth token`)

- **Google service-account JSON key** (only needed with `--drive_url`)
  - Create a service account in Google Cloud.
  - Enable the _Drive API_ on that project.
  - Download the key as JSON and place it at
    `~/.config/gspread_pandas/google_secret.json`.
  - Share the spreadsheet with the service-account address.

## Running the script

```bash
# Preview who is already invited and who would be invited.
dev_scripts_helpers/github/invite_gh_contributors.py \
    --csv_file  </path/to/users.csv> \
    --org_name  causify-ai \
    --repo_name tutorials \
    --dry_run

# Send the invitations.
dev_scripts_helpers/github/invite_gh_contributors.py \
    --drive_url "https://docs.google.com/spreadsheets/d/..." \
    --org_name  causify-ai \
    --repo_name tutorials

# Invite a few users passed on the command line, with read-only access.
dev_scripts_helpers/github/invite_gh_contributors.py \
    --add_gh_user alice \
    --add_gh_user bob \
    --org_name  causify-ai \
    --repo_name tutorials \
    --permission pull
```

- **`--drive_url`/`--csv_file`/`--add_gh_user`**: the users to invite. Pass only
  one of them.
  - `--drive_url` and `--csv_file` take a Google Sheet URL or a CSV file
    containing a column named `GitHub user`.
  - `--add_gh_user` takes one GitHub user name. Repeat it to invite many users.
- **`--org_name` / `--repo_name`**: where the invitations will be sent.
- **`--permission`**: permission granted to the invited users (default
  `write`). Use `pull` for read-only access.
- **`--skip_invited`** (default): invite only the difference between the passed
  users and the users already invited, i.e., collaborators or users with a
  pending invitation. Use `--no_skip_invited` to invite all the passed users.
- **`--dry_run`**: report who is already invited and who would be invited,
  without sending any invitation.
- Increase `-v` to `DEBUG` for verbose logs.
