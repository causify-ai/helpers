    out_file_name = "./tmp.run_pandoc_out.tex"
---
description: Split the current Git branch / PR in small a
---

# Goal

- Propose how to split the current Git branch / PR into small PRs to minimize:
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

## Step 2: Read the changes in the current Git branch

- Analyze the changes and propose a set of PRs that decompose the changes in
   coherent and tightly coupled changes

- Prefer PRs that have the changes to an entire file instead of having to split
  changes in a file across multiple PRs

- Make sure that changes to files and their testing files are in the same PR

- Merge low risk / complexity PRs so that there are fewer PRs even if the content
  of the resulting PR is the sum of multiple simpler ones
  - In this case, the description is multiple bullets explain what each smaller
    unit does

## Step 3: Order the PRs

- Start with the PRs that have low risk

## Step 4: Create pytest Command

- For each PR create a command with pytest command to run to exercise the changes
  by running the tests in all the modified files

## Step 5: Report the output in the following format

- Create a file `github_PR_plan.md` with the plan to split the PRs, following
  strictly the format in `.claude/templates/github_PR_plan.template.md`
- Run the linter
  ```
  > lint_txt.py -i github_PR_plan.md
  ```
