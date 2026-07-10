---
description: Split the current changes in a Git client in small cohesive PRs to simplify merging
---

# Goal

- Propose how to split the changes between current `HEAD` of the branch and
  `origin/master` into small PRs to minimize:
  - The review complexity
  - The risk of breaking the unit tests

- If the task is not perfectly clear or complex, you MUST not perform it, but ask
  for clarifications and create a plan for review
  - Create a `plan.md` with 5 bullet points explaining what the plan is

# Workflow

## Step 1: Read rules

- Read rules about:
  - Coding: `.claude/skills/coding.rules.md`
  - Unit tests: `.claude/skills/testing.rules.md`

## Step 2: Read the changes in the current Git client

- Obtain the files that need to be merged with
  ```bash
  git diff --name-status origin/master HEAD
  ...
  ```

- Analyze the difference between the current client and `master` (or
  `origin/master`):
  ```bash
  git diff master...HEAD --name-only
  # or if master is not available locally:
  git diff origin/master...HEAD --name-only
  ```

## Step 3: Propose PRs
- Propose a set of PRs that decompose the changes in the current Git client, so
  that there are coherent and tightly coupled changes

- Prefer PRs that have the changes to an entire file instead of having to split
  changes in a file across multiple PRs

- Make sure that changes to files and their testing files are in the same PR

- Merge low risk / complexity PRs so that there are fewer PRs even if the content
  of the resulting PR is the sum of multiple simpler ones
  - In this case, the description is multiple bullets explain what each smaller
    unit does

## Step 4: Order the PRs
- Start with the PRs that have low risk and touch most files

## Step 5: Create pytest Command

- For each PR create:
  - A file `pr<NUM>.files.txt` with the files changed, e.g.,
    ```
    .claude/skills
    .claude/templates
    .claude/notify.sh
    .claude/settings.local.json
    ```
  - A file `pr<NUM>.pytest.sh` with the pytest command to run to exercise the
    changes by running the tests in all the modified files and make sure the PR
    is running successfully, e.g.,
    ```bash
    #!/bin/bash
    pytest_log \
      dev_scripts_helpers/coding_tools/test \
      dev_scripts_helpers/dockerize/test \
      linters2/test \
      $@
    ```
  - Make this script executable with `chmod +x pr<NUM>.pytest.sh`

## Step 6: Report the output in the following format

- Create a file `github_PR_plan.md` with the plan to split the PRs, following
  strictly the format in `.claude/templates/github_PR_plan.template.md`
- If the file `github_PR_plan.md` already exists then updated it removing
  the PRs already merged based on the current `i git_files` and the `git log`
- Run the linter on `github_PR_plan.md`
  ```
  > lint_txt.py -i github_PR_plan.md
  ```
