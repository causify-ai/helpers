<!-- toc -->

- [Inviting GitHub Collaborators from Google Sheets](#inviting-github-collaborators-from-google-sheets)
  * [Prerequisites](#prerequisites)
  * [Running the script](#running-the-script)

<!-- tocstop -->

# Inviting GitHub Collaborators from Google Sheets

## Prerequisites

- **GitHub personal‑access token** (PAT) with the classic **`repo`** scope, or a
  fine‑grained token granting Repository administration for the target
  repository.

  ```bash
  export GH_PAT=github_pat_...
  ```

- **Google service‑account JSON key**
  - Create a service account in Google Cloud.
  - Enable the _Drive API_ on that project.
  - Download the key as JSON and place it at `/app/DATA605/google_secret.json`
    (or change the path in the script).
  - Share the spreadsheet with the service‑account address.

## Running the script

```bash
dev_scripts_helpers/github/invite_gh_contributors.py \
    --drive_url "https://docs.google.com/spreadsheets/d/..." \  # or  --csv_file  </path/to/users.csv>
    --gh_token  "$GH_PAT" \
    --org_name  causify-ai \
    --repo_name tutorials \
    --log_level 20          # INFO
```

- **`--drive_url`/`--csv_file`**: full URL of the Google Sheet containing a
  column named `GitHub user`.
- **`--gh_token`**: your PAT (or set `GH_PAT` and pass `--gh_token "$GH_PAT"`).
- **`--org_name` / `--repo_name`**: where the invitations will be sent.
- Increase `--log_level` to `10` for verbose debug logs.
