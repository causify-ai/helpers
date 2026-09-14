# Preventing bounty-spam bot contributions

<!-- toc -->

- [Background](#background)
- [Command-line mitigations](#command-line-mitigations)
  * [Interaction limits (block new accounts)](#interaction-limits-block-new-accounts)
  * [Branch protection / required review](#branch-protection--required-review)
  * [Repo settings sync tool (already in the repo)](#repo-settings-sync-tool-already-in-the-repo)
- [Repo-content mitigations](#repo-content-mitigations)
- [Weekly detection scan](#weekly-detection-scan)
- [Manual triage (what we did for the 2026-09-09/10 wave)](#manual-triage-what-we-did-for-the-2026-09-0910-wave)

<!-- tocstop -->

## Command-line mitigations

### Interaction limits (block new accounts)

Blocks anyone who is not an existing contributor/collaborator from opening
issues or PRs, for a chosen period:

```bash
> gh api -X PUT repos/causify-ai/helpers/interaction-limits \
    -f limit=existing_users \
    -f expiry=one_month

> gh api -X PUT repos/causify-ai/tutorials/interaction-limits \
    -f limit=existing_users \
    -f expiry=one_month
```

- `limit` options: `existing_users`, `contributors_only`, `collaborators_only`
- Check current state:
  ```bash
  > gh api repos/causify-ai/helpers/interaction-limits
  > gh api repos/causify-ai/tutorials/interaction-limits
  ```
- As of 2026-09-10, `causify-ai/helpers` already has this active
  (`existing_users`, expires 2026-10-10) — renew before it lapses.
  `causify-ai/tutorials` has none set (`{}`) — run the command above for it

### Branch protection / required review

Live settings can be inspected with:

```bash
> gh api repos/causify-ai/helpers/branches/master/protection
```

As of 2026-09-10, `required_approving_review_count` is `0` and
`require_code_owner_reviews` is `false` on `master` — i.e. a PR can merge
without any human approval. Tighten with:

```bash
> gh api -X PATCH repos/causify-ai/helpers/branches/master/protection/required_pull_request_reviews \
    -f required_approving_review_count=1 \
    -F require_code_owner_reviews=true
```

Add a `CODEOWNERS` file so "code owner review" actually maps to a real
gatekeeper:

```bash
> mkdir -p .github
> echo '* @gpsaggese' > .github/CODEOWNERS
```

### Repo settings sync tool (already in the repo)

`dev_scripts_helpers/github/sync_gh_repo_settings.py` (dockerized version:
`dockerized_sync_gh_repo_settings.py`) applies
`dev_scripts_helpers/github/settings/common_repo_settings.yaml`, which
already specifies `required_approving_review_count: 1` and
`require_code_owner_reviews: true` — it is just not applied to the live repo
yet. Run it instead of hand-crafted `gh api` calls to keep settings in one
place:

```bash
> dev_scripts_helpers/github/sync_gh_repo_settings.py \
    --input_file dev_scripts_helpers/github/settings/common_repo_settings.yaml \
    --repo_name helpers \
    --org_name causify-ai
```

## Repo-content mitigations

- `CONTRIBUTING.md` (already staged on the `gp` branch): state plainly that
  contributions are only accepted from invited/onboarded users, and link to
  the real bounty process instead of leaving bounty amounts free-floating in
  public issues
- `.github/ISSUE_TEMPLATE/config.yml` with `blank_issues_enabled: false`,
  plus a structured template (checkboxes, no free-text "fund this?" field) —
  removes the easy free-text surface the bots filled in
- Keep using `invite_gh_contributors.py` /
  `dockerized_invite_gh_contributors.py` as the only path to real
  collaborator status, so "existing_users" interaction limits actually track
  real invitees

## Weekly detection scan

```bash
> gh issue list -R causify-ai/helpers --search "bounty" --state all \
    --json number,title,state,author,url,createdAt --limit 100
```

Cross-check any hits against known accounts, then check account age /
followers for the rest:

```bash
> gh api users/<login> --jq '[.login, .created_at, .followers, .public_repos] | @tsv'
```

## Manual triage (what we did for the 2026-09-09/10 wave)

1. Listed PRs by author, matched against a curated `invalid_users.md` list
2. `gh pr close <n> -R causify-ai/helpers --comment "Contributions from not invited users"`
   for every open PR from those users
3. Searched issues for "bounty", cross-referenced authors against the same
   PR-spam accounts plus account-age/follower signals
4. `gh issue close <n> -R causify-ai/helpers --comment "Contributions from not invited users"`
   for every open issue in the confirmed wave
