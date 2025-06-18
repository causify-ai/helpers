# The Git Branch Copy Workflow

<!-- toc -->

- [Introduction](#introduction)
- [Workflow Explanation](#workflow-explanation)
- [Usage Instructions](#usage-instructions)
  * [Example](#example)
- [Alternative Manual Workflow](#alternative-manual-workflow)
  * [Using invoke `git_create_patch`](#using-invoke-git_create_patch)
  * [Known Limitations](#known-limitations)
  * [Future Improvements](#future-improvements)

<!-- tocstop -->

## Introduction

- The `git_branch_copy` `invoke` workflow creates a new Git branch derived from
  the current branch and copies its content exactly
- It's primarily useful in scenarios where a large PR (Pull Request) needs to be
  split into smaller, independently mergeable PRs to improve code review
  efficiency and reduce integration complexity
- This approach allows to:
  - Develop a large feature in one-shot, but merge it in chunks
  - Easily extract a sub-PR, since often "removing" code chunks is simpler than
    "adding" code chunks one by one, e.g., by reverting an entire file
  - Overlap developing and testing / reviewing
  - Make it simple to extract a sub-PR and then merge it back into the feature
    branch easily

## Workflow Explanation

- The workflow executes the following operations:
  - Cleans up untracked files in the working directory
  - Optionally merges the latest changes from `master` before creating the new
    branch
  - Creates and switches to a new branch
    - Automatically generates a suitable branch name if not explicitly provided
    - Validates the new branch name according to established naming conventions,
      e.g, `{Repo}Task{Number}_{Description}`
  - Squash merge changes from the current branch into the new branch
    - Changes are staged, but uncommitted, to allow developers to selectively
      stage, commit, and push specific parts.

## Usage Instructions

- Go to the target branch to merge
  ```bash
  > git checkout CmTask5874_Document_PR_flow
  ```

- You can execute the workflow with one of these command:

  ```bash
  # Create new branch with an automatically generated name (e.g., `CmTask5874_Document_PR_flow_02`).
  > i git_branch_copy

  # Create new branch with given name.
  > i git_branch_copy --new-branch-name="CmTask5874_PR_flow_Images"

  # Create a new branch without merging `master`.
  > i git_branch_copy --skip-git-merge-master --new-branch-name="CmTask5874_PR_flow_Images"

  # Create a new branch without checking for naming conventions.
  > i git_branch_copy --new-branch-name="wrongname_123" --no-check-branch-name
  ```

### Example

- Consider the case where we are working on a large feature branch
  `CmTask5874_Document_PR_flow`
- For various reasons we might want to extract and merge just a few files, e.g.,
  - The regression tests are not passing and we want to test and merge only a
    subset of changes
  - The branch contains unrelated changes (e.g., while implementing a feature,
    we ended up fixing another issue)
  - The PR is too complex to review in one shot and we want to break it down in
    reviewable pieces

- Rather than merging the main PR, we create one or more children PRs, and merge
  them into `master` one at a time

- Step 1: Make sure your branch is up to date with origin

  ```bash
  # First switch to your feature branch.
  > git checkout CmTask5874_Document_PR_flow

  # Make sure that the branch is up-to-date with master.
  > i git_merge_master

  # Commit and push the changes that you have made to the branch.
  > git commit -m "Merge"
  > git push

  # Check the diff between your branch and master.
  > i git_branch_diff_with -t base --only-print-files
  ```

- The output looks like:
  ```bash
  INFO: > cmd='/data/sameepp/src/venv/amp.client_venv/bin/invoke git_branch_diff_with -t base --only-print-files'
  04:58:35 - INFO  lib_tasks_git.py _git_diff_with_branch:726
  ###############################################################################
  # files=3
  ###############################################################################
  04:58:35 - INFO  lib_tasks_git.py _git_diff_with_branch:727
  ./figs/development/Fig1.png
  ./figs/development/Fig2.png
  docs/work_tools/all.development.how_to_guide.md
  04:58:35 - WARN  lib_tasks_git.py _git_diff_with_branch:732             Exiting as per user request with --only-print-files
  ```

- As shown above, three files have been modified

- Suppose we only want to partially merge this PR, specifically, just the `.png`
  files, while continuing development in the main feature branch.

- Step 2: Create a new branch (e.g., `CmTask5874_Document_PR_flow_02`) derived
  from our feature branch `CmTask5874_Document_PR_flow`

  ```bash
  # Create a derived branch from the feature branch.
  > i git_branch_copy
  INFO: > cmd='/data/sameepp/src/venv/amp.client_venv/bin/invoke git_branch_copy'
  git clean -fd
  invoke git_merge_master --ff-only
  From github.com:cryptokaizen/cmamp
  e59affd79..d6e6ed8e4  master     -> master
  INFO: > cmd='/data/sameepp/src/venv/amp.client_venv/bin/invoke git_merge_master --ff-only'
  ## git_merge_master:
  ## git_fetch_master:
  git fetch origin master:master
  git submodule foreach 'git fetch origin master:master'
  git merge master --ff-only
  Already up to date.
  07:04:46 - INFO  lib_tasks_git.py git_branch_copy:599                   new_branch_name='CmTask5874_Document_PR_flow_2'
  git checkout master && invoke git_branch_create -b 'CmTask5874_Document_PR_flow_2'
  Switched to branch 'master'
  Your branch is up to date with 'origin/master'.
  INFO: > cmd='/data/sameepp/src/venv/amp.client_venv/bin/invoke git_branch_create -b CmTask5874_Document_PR_flow_2'
  ## git_branch_create:
  07:05:00 - INFO  lib_tasks_git.py git_branch_create:413                 branch_name='CmTask5874_Document_PR_flow_2'
  git pull --autostash --rebase
  Current branch master is up to date.
  Switched to a new branch 'CmTask5874_Document_PR_flow_2'
  remote:
  remote: Create a pull request for 'CmTask5874_Document_PR_flow_2' on GitHub by visiting:
  remote:      https://github.com/cryptokaizen/cmamp/pull/new/CmTask5874_Document_PR_flow_2
  remote:
  To github.com:causify-ai/cmamp.git
  [new branch] CmTask5874_Document_PR_flow_2 ->
  CmTask5874_Document_PR_flow_2 git checkout -b CmTask5874_Document_PR_flow_2
  git push --set-upstream origin CmTask5874_Document_PR_flow_2 Branch
  'CmTask5874_Document_PR_flow_2' set up to track remote branch
  'CmTask5874_Document_PR_flow_2' from 'origin'. git merge --squash --ff
  CmTask5874_Document_PR_flow && git reset HEAD Updating d6e6ed8e4..a264a6f30
  Fast-forward Squash commit -- not updating HEAD
  docs/work_tools/figs/development/Fig1.png | Bin 27415 -> 0 bytes
  docs/work_tools/figs/development/Fig2.png | Bin 35534 -> 0 bytes 2 files
  changed, 0 insertions(+), 0 deletions(-) delete mode 100644
  docs/work_tools/figs/development/Fig1.png delete mode 100644
  docs/work_tools/figs/development/Fig2.png Unstaged changes after reset: D
  docs/work_tools/figs/development/Fig1.png D
  docs/work_tools/figs/development/Fig2.png
  ```

- Step 3: After running the command, a new branch
  `CmTask5874_Document_PR_flow_2` is created, containing all changes from the
  original feature branch.

  ```bash
  > git status
  On branch CmTask5874_Document_PR_flow_2
  Your branch is up to date with 'origin/CmTask5874_Document_PR_flow_2'.

  Untracked files:
  (use "git add <file>..." to include in what will be committed)
      ./figs/development/Fig1.png
      ./figs/development/Fig2.png
      docs/work_tools/all.invoke_workflows.how_to_guide.md
  ```

- You can now stage and commit only the files you want to merge (e.g., the
  `.png` files), and proceed to create a PR to merge those changes into `master`
  ```bash
  # Add, commit and push only the required files.
  > git add ./figs/development/Fig1.png ./figs/development/Fig2.png
  > git commit -m "Checkpoint"
  > git push origin CmTask5874_Document_PR_flow_2
  ```
- From this you can create a PR, test it, review it, and merge it

- Once the chunk is merged into `master`, you can go to the father branch and
  merge `master`
  ```bash
  > git checkout CmTask5874_Document_PR_flow
  > i git_merge_master
  > git commit -am "Merge"
  > git push
  ```
- Note that the merge it's typically very simple, since the incoming code is the
  same one that is already in the branch

## Alternative Manual Workflow

- You can also manually extract part of a PR using patch-based workflows or
  squash merging.

### Using invoke `git_create_patch`

- If you're working with multiple Git clients or prefer working outside your
  development tree:

  ```bash
  # In your feature branch:
  > i git_patch_create --branch

  # Copy the patch file to a clean Git client or switch to `master`
  > git checkout master

  # Apply the patch generated earlier
  > git apply ~/patch.amp.8f9cda97.20210609_080439.patch

  # The patch should apply cleanly. If you get conflicts, your feature branch may not be up-to-date with `master`.

  # Clean up unwanted files before committing
  > git diff
  > git checkout master -- files/to/revert

  # Commit and push selected changes
  > git commit -m "Partial merge from feature branch"
  > git push

  # Create a PR to trigger GitHub tests
  > i gh_create_pr --no-draft

  # Run regression tests
  > i run_fast_tests

  # Merge PR into `master`

  # Return to your feature branch and merge updates from `master`
  > git checkout CmTask5874_Document_PR_flow
  > git pull
  ```

### Known Limitations

- Currently, the `use_patch` option for creating branches via patches is
  unimplemented and reserved for future enhancements
- The workflow doesn't explicitly handle merge conflicts during the squash merge
  step, manual resolution may be required

### Future Improvements

- Implement the `use_patch` option to support patch-based branch creation
- Introduce enhanced automation for conflict resolution and interactive conflict
  handling during branch operations
- Provide options to handle specific file types or directories selectively
  during branch creation
