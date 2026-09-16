### [ ] Reorganize and test git/gh invoke tasks

* Repo: helpers only
- [x] helpers (https://github.com/causify-ai/helpers)

* Problem
- The `git_*`/`gh_*` invoke tasks in `helpers/lib_tasks/lib_tasks_git.py` and
  `helpers/lib_tasks/lib_tasks_gh.py` are almost entirely untested: only
  `git_patch_create` and a handful of `gh_*` helpers (e.g.
  `_get_gh_issue_title`, `gh_get_overall_build_status_for_repo`) have tests
  today
- Task bodies mix argument parsing, business logic, and `git`/`gh` subprocess
  calls in one function, so there is no pure logic to unit test without
  mocking the whole world
- Parameters are inconsistent across tasks: only `git_branch_create`,
  `git_branch_next_name`, `gh_issue_title`, `gh_issue_create`, and
  `gh_create_pr` accept `repo_short_name`; only `git_merge_master`,
  `git_clean`, `git_branch_diff`, `git_backup`, and `gh_delete_workflow_runs`
  accept `dry_run`
- `gh_watch` is defined in `lib_tasks_git.py` instead of `lib_tasks_gh.py`
- `git_branch_create --issue-id X --suffix Y` (`lib_tasks_git.py:609`)
  requires the caller to manually guess a free suffix, even though
  `hgit.get_branch_next_name` (`helpers/hgit.py:273`) already computes the
  next free one and is already used by `git_branch_next_name`
  (`lib_tasks_git.py:905`)

* Solution

- [ ] PR1: Let `git_branch_create` auto-pick the next free suffix
  - When `--issue-id` is given and `--suffix` is omitted, call
    `hgit.get_branch_next_name(curr_branch_name=<issue title>)` (same helper
    `git_branch_next_name` already uses) instead of requiring `--suffix`
  - Keep current behavior when `--suffix` is given explicitly: fail with
    `Branch '<name>' already exists` if that exact suffix is taken (verify
    this with a test, don't just assert it works)

- [ ] PR2: Add unit tests for `git_*`/`gh_*` invoke tasks
  - Cover the untested tasks in `lib_tasks_git.py` (`git_pull`,
    `git_fetch_master`, `git_merge_master`, `git_clean`,
    `git_add_all_untracked`, `git_files`, `git_branch_files`,
    `git_branch_create`, `git_branch_delete_merged`, `git_branch_rename`,
    `git_branch_next_name`, `git_branch_copy`, `git_branch_subset_copy`,
    `git_branch_diff`, `git_repo_copy`, `git_branches`,
    `git_branch_is_merged`, `git_backup`, `git_fix_perms`) and in
    `lib_tasks_gh.py` (`gh_login`, `gh_workflow_list`, `gh_workflow_run`,
    `gh_create_pr`, `gh_publish_buildmeister_dashboard_to_s3`,
    `gh_delete_workflow_runs`, `gh_create_mock_fixture`)
  - For tasks whose body is mostly `git`/`gh` subprocess calls, use
    `hunit_test_utils.assert_sys_calls` (imported as `hunteuti`, per existing
    convention in `lib_tasks_git.py:28`) against a mocked context, following
    `.claude/skills/testing.rules.md`
  - For tasks with non-trivial computation (e.g. suffix/branch-name logic),
    extract it into a private `_foo` helper first (pattern already used for
    `_delete_branches`, `_get_gh_issue_title`, `_check_if_pr_exists`) and
    test the helper directly instead of the `@task`-decorated wrapper

- [ ] PR3: Factor invoke bodies with heavy logic into standalone scripts
  - Scope: only tasks with non-trivial logic beyond a couple of subprocess
    calls — `git_branch_create`, `git_patch_create`, `git_branch_diff`,
    `git_branch_subset_copy`, `git_backup` — not every task in the file
  - Move the logic into a script under `dev_scripts_helpers/git/` (mirroring
    `dev_scripts_helpers/git/git_create_issue_and_branch.py`), leaving the
    `@task` function as a thin pass-through that builds the CLI invocation

- [ ] PR4: Unify parameter conventions across `git_*`/`gh_*` tasks
  - Add `--repo-short-name` to tasks that operate against a specific GitHub
    repo but currently lack it (e.g. `gh_workflow_list`, `gh_workflow_run`,
    `gh_publish_buildmeister_dashboard_to_s3`, `gh_delete_workflow_runs`)
  - Add `--dry-run` to tasks with side effects that currently lack it (e.g.
    `git_pull`, `git_fetch_master`, `git_add_all_untracked`,
    `git_branch_create`, `git_branch_delete_merged`, `git_branch_rename`,
    `git_branch_copy`, `git_branch_subset_copy`, `git_repo_copy`,
    `gh_create_pr`)
  - Move `gh_watch` from `lib_tasks_git.py` to `lib_tasks_gh.py`

- [ ] PR5: Audit task naming for `<object>_<action>` consistency
  - List every `git_*`/`gh_*` task name and flag any that don't read as
    `<object>_<action>` (e.g. `git_roll_amp_forward`, `git_files` vs.
    `git_branches` for singular/plural consistency)
  - Propose renames with `invoke.rename` or equivalent, updating all call
    sites and docs
  - ❓ Needs explicit sign-off before renaming anything, since renames break
    muscle memory / scripts that call these tasks by name

- [ ] PR6: Update documentation
  - docs/tools/all.invoke_workflows.how_to_guide.md
  - docs/tools/git/all.git.how_to_guide.md
  - docs/work_organization/all.use_github.how_to_guide.md
  - docs/tools/all.invoke_git_branch_copy.how_to_guide.md
