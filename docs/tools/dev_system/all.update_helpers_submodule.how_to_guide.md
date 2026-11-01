<!-- toc -->

- [How to Update the `helpers` Submodule Pointer](#how-to-update-the-helpers-submodule-pointer)
  * [What It Does](#what-it-does)
  * [How the Workflow Works](#how-the-workflow-works)
  * [Set Up the Workflow in a Super-Repo](#set-up-the-workflow-in-a-super-repo)
  * [Run the Workflow Manually](#run-the-workflow-manually)
  * [Update the Pointer Manually](#update-the-pointer-manually)
  * [Troubleshooting](#troubleshooting)

<!-- tocstop -->

# How to Update the `helpers` Submodule Pointer

## What It Does

- A super-repo includes `helpers` as the submodule `helpers_root`
  - The super-repo stores only a pointer, i.e., the commit hash of `helpers` it
    uses
  - The pointer does not move when `helpers` changes
- The GitHub Action `update_helpers_submodule.yml` moves the pointer forward
  - It runs the regressions with the new `helpers` code first
  - It commits and pushes the new pointer only if the regressions pass
  - If the regressions fail, the pointer stays where it is and the run fails
- Existing implementations:
  - `//csfy`: `.github/workflows/update_helpers_submodule.yml`, regressions run
    in Docker with `invoke run_fast_tests`
  - `//umd_classes`: `.github/workflows/update_helpers_submodule.yml`,
    regressions run without Docker with `pytest_log`
- The workflow is not in `helpers_root/.github/workflows`
  - The `helpers` repo would run it on itself, where there is no submodule
  - Each super-repo keeps its own copy, since it defines its own regressions

## How the Workflow Works

- Triggers:
  - `schedule`: every day at 1:00 am UTC, even if there are no commits
  - `workflow_dispatch`: manual run from the Actions tab
- Steps:
  1. Check out the super-repo with its submodules and the full history
  2. Fetch `master` of `helpers` inside `helpers_root` and compare it with the
     current pointer
     - Same commit: the pointer is up to date and all the next steps are skipped
     - Pointer is an ancestor of `master`: check out `master` in `helpers_root`
       and continue
     - Pointer is not an ancestor of `master`: print a warning and skip, so that
       a pointer set on purpose to a feature branch of `helpers` is not moved
       backwards
  3. Run the regressions of the super-repo against the new `helpers` code
  4. Run `git add helpers_root`, commit with the message `Update helpers repo`,
     and run `git push`
- The commit contains only the pointer
  - Other files changed by the tests are not committed
- Only one run at a time is allowed (`concurrency` group)
- If `git push` is rejected because the super-repo moved during the tests, the
  run fails and the next scheduled run retries

## Set Up the Workflow in a Super-Repo

- Copy `.github/workflows/update_helpers_submodule.yml` from an existing
  super-repo
  - Copy the file as is, do not use a symbolic link, since GitHub Actions does
    not resolve symbolic links in `.github/workflows`
- Replace the regressions step with the regressions of the super-repo
  - Docker-based repo: use `invoke run_fast_tests`
    - Add the steps to configure AWS, log in to GHCR, install
      `.github/gh_requirements.txt`, and run `invoke docker_pull`, as in
      `helpers_root/.github/workflows/common_run_tests.yml`
  - Repo without Docker: use `pytest_log` on the dirs with tests
    - Keep the command in sync with the one in `fast_tests.no_docker.yml`
- Set the permissions and secrets:
  - The workflow needs `contents: write` to push
  - Define the secret `GH_ACTION_ACCESS_TOKEN` (see
    `docs/tools/dev_system/all.create_a_super_repo_with_helpers.how_to_guide.md`)
    - If the secret is not defined, the workflow falls back to `GITHUB_TOKEN`
    - A push done with `GITHUB_TOKEN` does not trigger other workflows, so the
      regressions do not run on the pointer commit
- If the default branch is protected:
  - The bot must be allowed to push to the branch, or `git push` is rejected
  - Alternatively, change the last step to open a PR
- Optional: report failures on Slack
  - Add a `slackapi/slack-github-action` step with `if: failure()`, as in
    `common_run_tests.yml`
  - Define `SLACK_BUILD_NOTIF_CHANNEL_ID` and `SLACK_BOT_TOKEN`

## Run the Workflow Manually

- From the GitHub UI:
  - Go to `Actions > update_helpers_submodule > Run workflow` and select the
    default branch
- From the command line:
  ```bash
  > gh workflow run update_helpers_submodule.yml
  > gh run list --workflow update_helpers_submodule.yml --limit 3
  > gh run watch
  ```
- Run it on the default branch only
  - A run on another branch pushes the pointer commit to that branch

## Update the Pointer Manually

- Do this when the workflow fails and the Buildmeister needs to unblock the repo
  (see `docs/work_organization/all.buildmeister.how_to_guide.md`)
- Use the `invoke` task:
  ```bash
  > cd src/<super_repo>
  > git checkout master
  > git pull --recurse-submodules
  > invoke git_roll_submodule_forward --name helpers_root
  ```
  - The task:
    - Checks out `master` in the submodule and fast-forwards it to
      `origin/master`
    - Runs the regressions, only with `--run-regressions`
    - Commits the new pointer with the message `Roll helpers_root pointer forward`
    - Runs `git push`
  - Options:
    - `--name`: path of the submodule (e.g., `helpers_root`, `amp`)
    - `--branch`: branch of the submodule to roll forward to, `master` by default
    - `--run-regressions`: run `invoke run_fast_tests` before committing, and do
      not commit the pointer if they fail
    - `--dry-run`: print the commands without running them
  - Examples:
    ```bash
    > invoke git_roll_submodule_forward --name helpers_root --dry-run
    > invoke git_roll_submodule_forward --name helpers_root --run-regressions
    > invoke git_roll_submodule_forward --name amp
    ```
  - If the branch is protected, `git push` is rejected: use the manual steps
    below on a new branch and file a PR
  - `--run-regressions` needs a repo where `invoke run_fast_tests` works. In a
    repo with other regressions (e.g., `//umd_classes`) use the manual steps
- Or do the same steps by hand:
  ```bash
  > cd src/<super_repo>
  > git checkout master
  > git pull --recurse-submodules
  > cd helpers_root
  > git checkout master
  > git pull origin master
  > cd ..
  > git add helpers_root
  > git commit -m "Update helpers pointer"
  ```
- Run the regressions before pushing
- Then push, or file a PR if the branch is protected
  ```bash
  > git push
  ```

## Troubleshooting

- **Regressions fail with the new `helpers` code**
  - Cause: a change in `helpers` broke the super-repo
  - Fix: reproduce locally with the steps in "Update the Pointer Manually", fix the
    super-repo or `helpers`, and let the next run proceed
  - The pointer stays behind until the regressions pass, so the failure repeats
    every night
- **`git push` is rejected with `protected branch hook declined`**
  - Cause: the default branch requires a PR or status checks
  - Fix: allow the bot or the token owner to bypass the protection, or open a PR
- **Warning `helpers_root points to ..., which is not an ancestor of master`**
  - Cause: the pointer is on a commit that is not in `master` of `helpers`, e.g.,
    a feature branch
  - Fix: nothing, if intentional. Otherwise, move the pointer manually
- **The pointer commit does not trigger other workflows**
  - Cause: the push used `GITHUB_TOKEN`
  - Fix: define the secret `GH_ACTION_ACCESS_TOKEN`
- **Checkout fails to fetch `helpers_root`**
  - Cause: `.gitmodules` uses an SSH URL and the token cannot read `helpers`
  - Fix: use a token with read access to the `helpers` repo
