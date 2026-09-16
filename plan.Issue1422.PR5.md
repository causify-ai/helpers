# PR5: Audit `git_*`/`gh_*` task naming for `<object>_<action>` consistency

Per issue #1422, this is an audit only: it lists every `git_*`/`gh_*` invoke
task and flags names that don't read as `<namespace>_<object>_<action>`
(e.g. `git_branch_create` = `git` + `branch` + `create`). **No renames are
made in this PR** — renaming breaks muscle memory and any script that calls
these tasks by name, so the issue spec requires explicit sign-off first.

## Convention used as the yardstick

`<namespace>_<object>_<action>`, action last, e.g. `git_branch_create`,
`git_branch_rename`, `gh_issue_create`, `git_repo_copy`. Tasks with no
distinct object (the whole repo is the implicit object) are named
`<namespace>_<action>`, e.g. `git_pull`, `git_clean`, `gh_login` — these are
treated as consistent, not flagged.

## `lib_tasks_git.py`

| Task | Reads as | Consistent? | Note |
|---|---|---|---|
| `git_pull` | action | yes | implicit object (repo) |
| `git_clean` | action | yes | implicit object (repo) |
| `git_backup` | action | yes | implicit object (repo) |
| `git_add_all_untracked` | action + qualifier | yes | verb-first but no sibling to conflict with |
| `git_patch_create` | object + action | yes | |
| `git_branch_create` | object + action | yes | |
| `git_branch_delete_merged` | object + action | yes | |
| `git_branch_rename` | object + action | yes | |
| `git_branch_copy` | object + action | yes | |
| `git_branch_subset_copy` | object + action | yes | |
| `git_branch_diff` | object + action | yes | "diff" used as verb |
| `git_repo_copy` | object + action | yes | |
| `git_branch_is_merged` | object + predicate | different style | predicate/query, not imperative-action; not wrong, just a distinct sub-style from the others |
| `git_fetch_master` | action + object | **flag** | verb-first (`fetch` + `master`); inconsistent with `git_branch_*`/`git_repo_copy` object-first style |
| `git_merge_master` | action + object | **flag** | same verb-first issue as `git_fetch_master` |
| `git_set_symlink_perms` | action + object | **flag** | verb-first; consistent *with* `git_reset_symlink_perms`/`git_fix_perms` (a self-consistent verb-first trio) but not with the dominant object-first style |
| `git_reset_symlink_perms` | action + object | **flag** | same as above |
| `git_fix_perms` | action + object | **flag** | same as above |
| `git_roll_amp_forward` | action, opaque | **flag** | explicitly called out in the issue; doesn't decompose into object+action at all |
| `git_files` | bare plural object, no action | **flag** | implicit action "list"; consistent with `git_branches` (see below) but not with the dominant object+action style |
| `git_branches` | bare plural object, no action | **flag** | same as `git_files`; also the only `branch`-family task using the plural form (all others use singular `branch_`) |
| `git_branch_files` | object + noun (not a verb) | **flag** | "files" is not an action; real action is "list"/"show" |
| `git_branch_next_name` | object + noun phrase (not a verb) | **flag** | real action is "get"/"compute" |
| `git_file_version` | object + noun (not a verb) | **flag** | real action is "get"/"show" |

Not in scope for this issue (no test/param request in the spec, listed for
completeness): `git_set_symlink_perms`, `git_reset_symlink_perms`,
`git_roll_amp_forward`, `git_file_version` were not in PR2's test list or
PR3/PR4's scope lists, so they're flagged here but untouched by this stack
so far.

## `lib_tasks_gh.py`

| Task | Reads as | Consistent? | Note |
|---|---|---|---|
| `gh_login` | action | yes | implicit object |
| `gh_watch` | action | yes | implicit object |
| `gh_workflow_list` | object + action | yes | |
| `gh_workflow_run` | object + action | yes | |
| `gh_issue_create` | object + action | yes | |
| `gh_issue_title` | object + noun (not a verb) | **flag** | real action is "get"/"print" |
| `gh_create_pr` | action + object | **flag, high-confidence** | same action ("create") as `gh_issue_create`, but opposite word order — a direct sibling inconsistency, not just a style preference |
| `gh_delete_workflow_runs` | action + object | **flag** | verb-first; inconsistent with `gh_workflow_list`/`gh_workflow_run` (object-first) |
| `gh_create_mock_fixture` | action + object | **flag** | verb-first |
| `gh_publish_buildmeister_dashboard_to_s3` | action + object + destination | **flag** | verb-first; also long/specific enough that a clean object-first rename is awkward |

## Proposed renames (pending sign-off — none applied)

Highest confidence first:

1. `gh_create_pr` → `gh_pr_create` (direct sibling mismatch with `gh_issue_create`)
2. `gh_delete_workflow_runs` → `gh_workflow_runs_delete` (or `gh_workflow_delete_runs`)
3. `gh_create_mock_fixture` → `gh_mock_fixture_create`
4. `git_branches` → `git_branch_list` (aligns with singular `branch_` family; would leave `git_files` as the only bare-plural, no-action task, or `git_files` could be renamed too — see below)
5. `git_branch_files` → `git_branch_list_files` or `git_branch_files_list`
6. `git_branch_next_name` → `git_branch_get_next_name`
7. `gh_issue_title` → `gh_issue_get_title`
8. `git_file_version` → `git_file_get_version`

Lower confidence / judgment calls (renaming these has a worse cost/benefit
since they're either very commonly typed, or a clean rename is awkward):

- `git_fetch_master`, `git_merge_master` — verb-first but read naturally as
  git-subcommand mirrors (`git fetch`, `git merge`); renaming to
  `git_master_fetch`/`git_master_merge` reads worse to a git user
- `git_set_symlink_perms`, `git_reset_symlink_perms`, `git_fix_perms` — a
  self-consistent verb-first trio; renaming only these three to match the
  rest of the file is possible (`git_symlink_perms_set`, etc.) but they read
  fine as-is and are less confusing internally than externally
- `git_roll_amp_forward` — opaque/legacy name; a rename needs someone who
  knows the original intent to propose a clearer name, not just a mechanical
  reorder
- `git_add_all_untracked` — reads fine as `git add` mirror, no sibling
  conflict
- `git_files` — bare plural like `git_branches`; only worth renaming if
  `git_branches` is also renamed, to keep the two consistent with each other
- `gh_publish_buildmeister_dashboard_to_s3` — long, specific, low call
  frequency; a clean object-first rename is clunky
  (`gh_buildmeister_dashboard_publish_to_s3`)

## Next step

**Waiting for explicit sign-off** on which of the above (if any) to actually
rename before touching any call sites/docs, per the issue's "❓ Needs
explicit sign-off before renaming anything" requirement.
